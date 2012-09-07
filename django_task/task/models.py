import uuid
import datetime
import time
from operator import itemgetter

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from taskw.utils import encode_replacements

PRIORITY_CHOICES = (
        (0, ''),  # unprioritized
        (1, 'L'),
        (2, 'M'),
        (3, 'H')
        )

PRIORITY_MAP = dict(PRIORITY_CHOICES)
PRIORITY_MAP_R = dict((v, k) for (k, v) in PRIORITY_CHOICES)


def get_or_create_task(**kwargs):
    """ Return an existing task or new task if it doesn't exist.

        This is intended to be exactly the same as `Model.objects.get_or_create()`
        except that the `track` kwarg is passed to `save`.
    """
    track = kwargs.pop('track', True)
    try:
        task = Task.objects.get(**kwargs)
    except Task.DoesNotExist:
        task = Task(**dict((k, v) for (k, v) in kwargs.items() if '__' not in k))
        task.save(track=track)

    return task


def encode_task(d):
    # until this gets merged to taskw
    def _encode_task(task):
        """ Convert a dict-like task to its string representation """
        # First, clean the task:
        task = task.copy()
        for k in task:
            for unsafe, safe in encode_replacements.iteritems():
                task[k] = task[k].replace(unsafe, safe)

        # Then, format it as a string
        return "[%s]\n" % " ".join([
            "%s:\"%s\"" % (k, v) for k, v in sorted(task.items(), key=itemgetter(0))
        ])
    d.pop('user', None)
    return _encode_task(d)


def undo(func):
    """ A decorator that wraps a given function to track the before
        and after states in the Undo table.
    """
    def _decorator(self, *args, **kwargs):
        track = kwargs.pop('track', True)
        if track:
            old = encode_task(self.todict())
            func(self, *args, **kwargs)
            new = encode_task(self.todict())
            if new != old:
                Undo.objects.create(old=old, new=new, user=self.user)
        else:
            func(self, *args, **kwargs)

    return _decorator


def datetime2ts(dt):
    """ Convert a `datetime` object to unix timestamp (seconds since epoch).
    """
    return int(time.mktime(dt.timetuple()))


class Priority(models.Model):
    weight = models.PositiveSmallIntegerField(choices=PRIORITY_CHOICES,
                                              unique=True)

    class Meta:
        ordering = ['-weight']

    def __unicode__(self):
        return unicode(self.get_weight_display())

    def to_taskw(self):
        return dict(PRIORITY_CHOICES)[self.weight]


class Profile(models.Model):
    user = models.OneToOneField(User)
    sort_task_columns = models.CharField(max_length=256, blank=True)
    task_columns = models.CharField(max_length=256, blank=True)


class Undo(models.Model):
    """ Representation of taskwarrior undo.data
    """
    user = models.ForeignKey(User)
    time = models.DateTimeField()
    new = models.TextField()
    old = models.TextField(blank=True, null=True)

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
                data += u'old %s' % undo.old
            data += u'new %s' % undo.new
            data += u'---\n'

        return data


class Annotation(models.Model):
    time = models.DateTimeField()
    data = models.TextField()

    class Meta:
        ordering = ['-time']

    def save(self, *args, **kwargs):
        if not self.time:
            self.time = datetime.datetime.now()

        super(Annotation, self).save(*args, **kwargs)

    def __unicode__(self):
        return u"%s %s" % (self.time.strftime('%m/%d/%Y'), self.data)


class Tag(models.Model):
    tag = models.CharField(max_length=256, unique=True)

    def __unicode__(self):
        return self.tag


class Project(models.Model):
    name = models.CharField(max_length=256, unique=True)

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ("task.views.detail_project", [str(self.id)])


class DirtyFieldsMixin(object):
    """ Mixin for Models to track whether a model is 'dirty'.
    """
    def __init__(self, *args, **kwargs):
        self._original_state = self._as_dict()

    def _as_dict(self):
        return self._todict()

    def _get_dirty_fields(self):
        new_state = self._as_dict()

        if not self.pk:
            return new_state

        missing = object()
        result = {}
        for key, value in new_state.iteritems():
            if value != self._original_state.get(key, missing):
                result[key] = value

        return result

    def _is_dirty(self):
        """ Return True if the data in the model is 'dirty', or
            not flushed to the db.
        """
        if self._get_dirty_fields():
            return True

        return False


class Task(models.Model, DirtyFieldsMixin):
    """ Representation of a `taskwarrior` task.
    """
    user = models.ForeignKey(User, null=True)
    uuid = models.CharField(max_length=64, unique=True)
    description = models.TextField()
    entry = models.DateTimeField()
    due = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=100)
    project = models.ForeignKey(Project, blank=True, null=True)
    tags = models.ManyToManyField(Tag, max_length=200, null=True, blank=True)
    priority = models.ForeignKey(Priority, null=True, blank=True)
    annotations = models.ManyToManyField(Annotation, null=True, blank=True)
    dependencies = models.ManyToManyField('self', symmetrical=False,
                                            null=True, blank=True)

    class Meta:
        get_latest_by = 'entry'
        ordering = ['-entry']

    def __init__(self, *args, **kwargs):
        models.Model.__init__(self, *args, **kwargs)
        DirtyFieldsMixin.__init__(self)

    def __unicode__(self):
        return self.description

    @models.permalink
    def get_absolute_url(self):
        return ("task.views.detail_task", [str(self.id)])

    @classmethod
    def fromdict(cls, d, track=False):
        due = d.get('due')
        if due is not None:
            due = datetime.datetime.fromtimestamp(int(due))

        end = d.get('end')
        if end is not None:
            end = datetime.datetime.fromtimestamp(int(end))

        entry = d.get('entry')
        if entry is not None:
            entry = datetime.datetime.fromtimestamp(int(entry))

        try:
            task = Task.objects.get(uuid=d['uuid'])
            task.description = d['description']
            task.status = d.get('status')
            task.entry = entry
            task.due = due
            task.end = end
            task.user = d['user']
        except Task.DoesNotExist:
            task = cls(
                description=d['description'],
                uuid=d.get('uuid'),
                status=d.get('status'),
                entry=entry,
                due=due,
                end=end,
                user=d['user'],
                )

        # add the priority
        task.set_priority(d.get('priority'), track=False)

        # add the project
        task.set_project(d.get('project'), track=False)

        # we have to save before we can add ManyToMany
        if not task.pk:
            task.save(track=track)

        # add the tags (for some reason it is a list of tags now and
        # not a comma-separated string --danny)
        for tag in d.get('tags', ''):
            if tag:
                task.add_tag(tag, track=False)

        # dependencies
        for dep in d.get('depends', '').split(','):
            if dep:
                task.add_dependency(dep, track=False)

        # add the annotations
        annotations = []
        for k, v in d.items():
            if k.startswith('annotation'):
                note = {}
                note['note'] = v
                ts = int(k.split('_')[1])
                note['time'] = datetime.datetime.fromtimestamp(ts)
                annotations.append(note)

        for note in annotations:
            note.update({'track': False})
            task.annotate(**note)

        task.save(track=track)

        return task

    @undo
    def set_priority(self, priority):
        if not priority:
            priority = ''

        if isinstance(priority, (str, unicode)):
            priority = PRIORITY_MAP_R[priority]

        pri, created = Priority.objects.get_or_create(weight=priority)
        self.priority = pri

    @undo
    def set_project(self, project):
        if not project:
            self.project = None
            return

        proj, created = Project.objects.get_or_create(name=project)
        self.project = proj

    @undo
    def add_tag(self, tag):
        tag, created = Tag.objects.get_or_create(tag=tag)
        self.tags.add(tag)

    @undo
    def remove_tag(self, tag):
        try:
            tag = Tag.objects.get(tag=tag)
        except Tag.DoesNotExist:
            return
        self.tags.remove(tag)

    @undo
    def annotate(self, note=None, time=None):
        annotation = Annotation.objects.create(data=note, time=time)
        self.annotations.add(annotation)

    @undo
    def add_dependency(self, task):
        if isinstance(task, (str, unicode)):
            # a uuid?
            task = get_or_create_task(uuid=task, track=False)

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

        if not self.priority:
            self.priority = Priority.objects.get_or_create(weight=0)[0]

        data = {}
        is_dirty = self._is_dirty()
        if self.pk and is_dirty:
            old = self._original_state
            data['old'] = encode_task(old)

        super(Task, self).save(*args, **kwargs)

        if track and is_dirty:
            # add to undo table
            data['new'] = encode_task(self.todict())
            data['user'] = self.user
            Undo.objects.create(**data)

        self._original_state = self._as_dict()

    def _todict(self):
        # TODO: This is ugly, i need  to find a better way...
        task = {}
        for fieldname in self._meta.get_all_field_names():
            if fieldname in ['task', 'id']:
                # skip these fields
                continue

            try:
                value = getattr(self, fieldname)
            except ValueError:
                value = None

            if value:
                if fieldname in ['end', 'entry', 'due']:
                    value = int(datetime2ts(value))
                elif isinstance(value, list):
                    value = ','.join(value)
                elif fieldname == 'dependencies':
                    value = ','.join([t.uuid for t in value.all().order_by('pk')])
                    if value:
                        task['depends'] = value
                    continue
                elif fieldname == 'annotations':
                    for annotation in value.all():
                        key = 'annotation_%s' % datetime2ts(annotation.time)
                        task[key] = annotation.data
                    continue
                elif fieldname == 'tags':
                    value = ','.join([t.tag for t in value.all()])

                if value and str(value):
                    task[fieldname] = str(value)

        return task

    def todict(self):
        d = self._todict()
        d.pop('user', None)  # not a valid field for taskwarrior
        return d

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
            data += encode_task(task.todict())

        return data


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)
