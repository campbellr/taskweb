import uuid
import datetime
import time

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

PRIORITY_CHOICES = (
        ('', None),
        ('H', 'High'),
        ('M', 'Medium'),
        ('L', 'Low')
        )


def task2str(task):
    """ Return a string suitable for the taskwarrior db
        Extracted from `taskw` (https://github.com/ralphbean/taskw)
    """
    return "[%s]\n" % " ".join([
        "%s:\"%s\"" % (k, v) for k, v in task.iteritems()
    ])


def datetime2ts(dt):
    """ Convert a `datetime` object to unix timestamp (seconds since epoch).
    """
    return int(time.mktime(dt.timetuple()))


class Profile(models.Model):
    user = models.OneToOneField(User)
    sort_task_columns = models.CharField(max_length=256, blank=True)
    task_columns = models.CharField(max_length=256, blank=True)


class Undo(models.Model):
    """ Representation of taskwarrior undo.data
    """
    user = models.ForeignKey(User)
    time = models.DateTimeField()
    new = models.CharField(max_length=200)
    old = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['time']

    def __unicode__(self):
        return u'<Undo: %s, %s, %s>' % (self.time, self.new, self.old)

    def save(self, *args, **kwargs):
        if not self.time:
            self.time = datetime.datetime.now()

        super(Undo, self).save(*args, **kwargs)

    @classmethod
    def fromdict(cls, d):
        undo = cls(
                user=d['user'],
                time=datetime.datetime.fromtimestamp(int(d['time'])),
                old=d.get('old'),
                new=d['new'],
               )

        undo.save()
        return undo

    @classmethod
    def serialize(cls):
        """ Serialze the table into a format expected by taskwarrior
        """
        data = ''
        for undo in cls.objects.all():
            data += u'time %s\n' % int(datetime2ts(undo.time))
            if undo.old:
                data += u'old %s\n' % undo.old
            data += u'new %s\n' % undo.new
            data += u'---\n'

        return data


class Annotation(models.Model):
    time = models.DateTimeField()
    data = models.TextField()

    def save(self, *args, **kwargs):
        if not self.time:
            self.time = datetime.datetime.now()

        super(Annotation, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.data


class Tag(models.Model):
    tag = models.CharField(max_length=256, unique=True)

    def __unicode__(self):
        return self.tag


class Task(models.Model):
    """ Representation of a `taskwarrior` task.
    """
    user = models.ForeignKey(User)
    uuid = models.CharField(max_length=64, unique=True)
    description = models.TextField()
    entry = models.DateTimeField()
    end = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=100)
    project = models.CharField(max_length=100, blank=True, null=True)
    tags = models.ManyToManyField(Tag, max_length=200, null=True, blank=True)
    priority = models.CharField(choices=PRIORITY_CHOICES, max_length=1,
                                null=True, blank=True)
    annotations = models.ManyToManyField(Annotation, null=True, blank=True)
    dependencies = models.ManyToManyField('self', symmetrical=False,
                                            null=True, blank=True)

    class Meta:
        get_latest_by = 'entry'
        ordering = ['-entry']

    def __unicode__(self):
        return self.description

    @classmethod
    def fromdict(cls, d, track=False):
        task = cls(
            description=d['description'],
            uuid=d['uuid'],
            project=d.get('project'),
            status=d['status'],
            entry=datetime.datetime.fromtimestamp(int(d['entry'])),
            priority=d.get('priority'),
            user=d['user'],
            )

        task.save(track=track)

        for tag in d.get('tags', '').split(','):
            task.add_tag(tag, track=track)

        return task

    def add_tag(self, tag, track=True):
        if not Tag.objects.filter(tag=tag):
            tag = Tag.objects.create(tag=tag)
        else:
            tag = Tag.objects.get(tag=tag)

        self.tags.add(tag)
        self.save(track=track)

    def remove_tag(self, tag, track=True):
        try:
            tag = Tag.objects.get(tag=tag)
        except Tag.DoesNotExist:
            return

        self.tags.remove(tag)
        self.save(track=track)

    def annotate(self, note, time=None):
        annotation = Annotation.objects.create(data=note, time=time)
        self.annotations.add(annotation)
        self.save()

    def add_dependency(self, task):
        if isinstance(task, str):
            # a uuid?
            task = Task.get(uuid=task)

        self.dependencies.add(task)

    def done(self):
        """ Mark a task as completed.
        """
        self.status = 'completed'
        self.end = datetime.datetime.now()
        self.save()

    def save(self, *args, **kwargs):
        """ Automatically populate optional fields if they haven't been
            specified in __init__.
        """
        track = kwargs.pop('track', True)

        if not self.uuid:
            self.uuid = str(uuid.uuid4())

        if not self.status:
            self.status = 'pending'

        if not self.entry:
            self.entry = datetime.datetime.now()

        super(Task, self).save(*args, **kwargs)

        if track:
            # add to undo table
            data = {}
            if self.pk:
                old = Task.objects.get(pk=self.pk)
                data['old'] = task2str(old.todict())

            data['new'] = task2str(self.todict())
            data['user'] = self.user
            Undo.objects.create(**data)

    def todict(self):
        # TODO: This is ugly, i need  to find a better way...
        task = {}
        for fieldname in self._meta.get_all_field_names():
            if fieldname in ['task', 'user', 'id']:
                # skip these fields
                continue

            value = getattr(self, fieldname)
            if value:
                if fieldname in ['end', 'entry']:
                    value = int(datetime2ts(value))
                elif isinstance(value, list):
                    value = ','.join(value)
                elif fieldname == 'user':
                    continue
                elif fieldname == 'dependencies':
                    value = ','.join([t.uuid for t in value.all()])
                elif fieldname == 'annotations':
                    for annotation in value.all():
                        key = 'annotation_%s' % datetime2ts(annotation.time)
                        task[key] = annotation.data
                    continue
                elif fieldname == 'tags':
                    value = ','.join([t.tag for t in value.all()])

                if value:
                    task[fieldname] = str(value)

        return task

    @classmethod
    def serialize(cls, status=None):
        """ Serialze the tasks to a string suitable for taskwarrior.
        """
        if status is None:
            tasks = cls.objects.order_by('entry')
        else:
            tasks = cls.objects.filter(status=status).order_by('entry')

        data = ''
        for task in tasks:
            data += task2str(task.todict())

        return data


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)
