from djblets.datagrid.grids import Column, DataGrid, DateTimeSinceColumn
from task.models import Task


class TaskDataGrid(DataGrid):
    id_ = Column('ID', sortable=True, shrink=True, field_name='id')
    entry = DateTimeSinceColumn('Age', sortable=True)
    project = Column('Proj', sortable=True, shrink=True)
    tags = Column('Tags', sortable=True, shrink=True)
    priority = Column('Pri', sortable=True, shrink=True)
    description = Column('Description', sortable=True)
    uuid = Column('uuid', sortable=True)
    user = Column('User', sortable=True, shrink=True)
    status = Column('Status', sortable=True, shrink=True)

    def __init__(self, request, queryset=Task.objects.all(), **kwargs):
        super(TaskDataGrid, self).__init__(request, queryset=queryset, **kwargs)
        self.default_sort = ['-id_']
        self.default_columns = ['id_', 'project', 'priority', 'tags', 'entry', 'description']
