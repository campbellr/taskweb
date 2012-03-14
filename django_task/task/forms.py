from django import forms

from task.models import Task, Tag, Project, Priority
from task import widgets


class TaskForm(forms.ModelForm):
    priority = forms.ModelChoiceField(queryset=Priority.objects.exclude(weight=0), required=False)
    class Meta:
        model = Task
        exclude = ('entry', 'uuid', 'end', 'status', 'annotations')
        widgets = {
                    'project': widgets.SelectWithPopUp,
                    'tags': widgets.MultipleSelectWithPopUp,
                    'due': widgets.JQueryDateWidget,
                  }


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
