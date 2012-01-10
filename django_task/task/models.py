import uuid
import datetime

from django.db import models


class ListField(models.CharField):
    """ Stores a python list as a comma-separated string.
    """
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if not value:
            return []
        return value.split(',')

    def get_prep_value(self, value):
        if value is None:
            return value

        return ','.join(value)


class Task(models.Model):
    """ Representation of a `taskwarrior` task.
    """
    uuid = models.CharField(max_length=64, primary_key=True, unique=True)
    description = models.TextField()
    entry = models.DateTimeField()
    end = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=100)
    project = models.CharField(max_length=100, blank=True, null=True)
    tags = ListField(max_length=200, null=True, blank=True)
    dependencies = models.ManyToManyField('self', symmetrical=False,
                                            null=True, blank=True)

    class Meta:
        get_latest_by = 'entry'
        ordering = ['-entry']

    def __unicode__(self):
        return self.description

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
        if not self.uuid:
            self.uuid = str(uuid.uuid4())

        if not self.status:
            self.status = 'pending'

        if not self.entry:
            self.entry = datetime.datetime.now()

        super(Task, self).save(*args, **kwargs)

    @classmethod
    def serialize(cls):
        """ Serialze the tasks to a string suitable for taskwarrior.
        """
