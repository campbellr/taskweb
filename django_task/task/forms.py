from django import forms

from task.models import Task, Tag, Project, Priority
from task import widgets

STATUS_CHOICES = (
        ('pending', 'pending'),
        ('completed', 'completed'),
        )


class TaskForm(forms.ModelForm):
    priority = forms.ModelChoiceField(queryset=Priority.objects.exclude(weight=0), required=False)
    status = forms.ChoiceField(choices=STATUS_CHOICES)

    class Meta:
        model = Task
        exclude = ('entry', 'uuid', 'end', 'annotations')
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
