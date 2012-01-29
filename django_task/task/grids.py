from django.db.models import Min
from django.utils.html import urlize

from djblets.datagrid import grids
from task.models import Task


class Column(grids.Column):
    def render_data(self, obj):
        value = super(Column, self).render_data(obj)
        if value is None:
            return ''

        return value


class IDColumn(grids.Column):
    """ `taskwarrior` represents id in sequence starting from 1, so
         this column emulates that by shifting the `Task` id column
         so they start at 1.
    """
    def render_data(self, obj):
        # This doesn't actually work unless db ids are
        # sequential...
        value = super(IDColumn, self).render_data(obj)
        min_id = Task.objects.aggregate(Min('id'))['id__min']
        return value - min_id + 1


class TagColumn(Column):
    def render_data(self, obj):
        value = super(TagColumn, self).render_data(obj)
        return ', '.join([t.tag for t in value.all()])


class ShortDateTimeSinceColumn(grids.DateTimeSinceColumn):
    """ Similar to the default `DateTimeSinceColumn` but only
        displays the most significant time. (eg: '1 hour ago' vs
        '1 hour, 3 minutes ago'
    """
    def render_data(self, obj):
        value = super(ShortDateTimeSinceColumn, self).render_data(obj)
        return value.split(',')[0]


class DescriptionWithAnnotationColumn(Column):
    def render_data(self, obj):
        description = super(DescriptionWithAnnotationColumn,
                            self).render_data(obj)
        annotations = [str(a) for a in obj.annotations.all()]
        value = description + "<br/>"
        for note in annotations:
            note = urlize(note)
            value += "&nbsp;" * 4 + note + "<br/>"

        return value


class TaskDataGrid(grids.DataGrid):
    id_ = IDColumn('ID', sortable=True, shrink=True, field_name='id')
    entry = ShortDateTimeSinceColumn('Age', sortable=True)
    due = grids.DateTimeColumn('Due', sortable=True)
    project = Column('Proj', sortable=True, shrink=True)
    tags = TagColumn('Tags', sortable=True)
    priority = Column('Pri', sortable=True, shrink=True)
    description = DescriptionWithAnnotationColumn('Description', sortable=True,
            expand=True)
    uuid = Column('uuid', sortable=True)
    user = Column('User', sortable=True, shrink=True)
    status = Column('Status', sortable=True, shrink=True)

    def __init__(self, request, queryset=Task.objects.all(), **kwargs):
        super(TaskDataGrid, self).__init__(request, queryset=queryset, **kwargs)
        self.default_sort = ['-id_']
        self.default_columns = ['id_', 'project', 'priority', 'tags', 'entry',
                                'due', 'description']
        self.profile_sort_field = 'sort_task_columns'
        self.profile_columns_field = 'task_columns'
