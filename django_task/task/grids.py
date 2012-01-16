from djblets.datagrid.grids import Column, DataGrid, DateTimeSinceColumn
from task.models import Task


class TaskDataGrid(DataGrid):
    id_ = Column('ID', sortable=True)
    entry = DateTimeSinceColumn('Age', sortable=True)
    project = Column('Proj', sortable=True)
    tags = Column('Tags', sortable=True)
    priority = Column('Pri', sortable=True)
    description = Column('Description', sortable=True)
    uuid = Column('uuid', sortable=True)
    user = Column('User', sortable=True)
    status = Column('Status', sortable=True)

    def __init__(self, request, queryset=Task.objects.all(), **kwargs):
        super(TaskDataGrid, self).__init__(request, queryset=queryset, **kwargs)
        self.default_sort = ['-id_']
        self.default_columns = ['id_', 'priority', 'tags', 'entry', 'description']
