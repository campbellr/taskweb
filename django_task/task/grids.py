from djblets.datagrid import grids
from task.models import Task


class Column(grids.Column):
    def render_data(self, obj):
        value = super(Column, self).render_data(obj)
        if value is None:
            return ''

        return value


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


class TaskDataGrid(grids.DataGrid):
    id_ = Column('ID', sortable=True, shrink=True, field_name='id')
    entry = ShortDateTimeSinceColumn('Age', sortable=True)
    project = Column('Proj', sortable=True, shrink=True)
    tags = TagColumn('Tags', sortable=True)
    priority = Column('Pri', sortable=True, shrink=True)
    description = Column('Description', sortable=True, expand=True)
    uuid = Column('uuid', sortable=True)
    user = Column('User', sortable=True, shrink=True)
    status = Column('Status', sortable=True, shrink=True)

    def __init__(self, request, queryset=Task.objects.all(), **kwargs):
        super(TaskDataGrid, self).__init__(request, queryset=queryset, **kwargs)
        self.default_sort = ['-id_']
        self.default_columns = ['id_', 'project', 'priority', 'tags', 'entry',
                                'description']
        self.profile_sort_field = 'sort_task_columns'
        self.profile_columns_field = 'task_columns'
