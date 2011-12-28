from django import forms

PRIORITY_CHOICES = (
        ('', None),
        ('H', 'High'),
        ('M', 'Medium'),
        ('L', 'Low')
        )

class TaskForm(forms.Form):
    description = forms.CharField()
    priority = forms.ChoiceField(choices=PRIORITY_CHOICES, required=False)
    project = forms.CharField(required=False)
    tags = forms.CharField(required=False)

class TaskDbUploadForm(forms.Form):
    completed = forms.FileField()
    pending = forms.FileField()
