""" Various tests for taskweb
"""
import os

from django.test import TestCase
from django.contrib.auth.models import User

from task.models import Task, Tag, Undo, Priority, Project
from task.util import parse_undo
from task.grids import IDColumn, DescriptionWithAnnotationColumn
from task import forms


class TaskTestCase(TestCase):
    def create_user(self, username='foo', passw='baz'):
        users = User.objects.filter(username=username)
        if users:
            return users[0]

        user = User.objects.create_user(username, 'foo@test.com', passw)
        user.save()
        return user


class TestForms(TaskTestCase):
    def test_task_form(self):
        user = self.create_user()
        tags = Tag.objects.create(tag='tag1')
        task = Task()
        d = {'priority': '', 'description': 'foobar',
                'user': '1', 'tags': ['1'],
                'status': 'pending'}
        form = forms.TaskForm(d)
        valid = form.is_valid()
        self.assertTrue(valid)
        task = form.save()

        # silly extra save() to
        # add proper undo info for m2m
        task.save()

        tdict = task.todict()
        self.assertEqual(tdict['description'], 'foobar')
        self.assertEqual(Undo.objects.count(), 2)

    def test_tag_form(self):
        d = {'tag': 'foobar'}
        form = forms.TagForm(d)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(len(Tag.objects.all()), 1)

    def test_project_form(self):
        d = {'name': 'project1'}
        form = forms.ProjectForm(d)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(len(Project.objects.all()), 1)


class TestGrids(TaskTestCase):
    def test_idcolumn(self):
        user = self.create_user()
        column = IDColumn('id_', field_name='id')
        for x in range(5):
            Task.objects.create(description='test %s' % x,
                                user=user)

        value = column.render_data(Task.objects.get(id=1))
        self.assertEqual(value, 1)

        for x in range(1, 3):
            Task.objects.get(id=x).delete()

        value = column.render_data(Task.objects.get(id=3))
        self.assertEqual(value, 1)

    def test_description_column(self):
        from django.utils.html import urlize

        annotation_str = 'testing urls: google.com'
        user = self.create_user()
        column = DescriptionWithAnnotationColumn('description',
                field_name='description')
        task = Task.objects.create(description='testing',
                                user=user)

        task.annotate(annotation_str)

        value = column.render_data(Task.objects.get(id=1))
        self.assertIn(urlize(annotation_str), value)


class TestTaskModel(TaskTestCase):
    def test_create_task_no_params(self):
        task = Task()

    def test_create_task_no_uuid(self):
        """ Verify that a `Task`s uuid field is automatically populated
            when not specified.
        """
        # description and user are the only required field
        user = self.create_user()
        task = Task(description='foobar', user=user)
        task.save()
        self.assertTrue(hasattr(task, 'uuid'))
        self.assertNotEqual(task.uuid, None)

    def test_create_task_with_uuid(self):
        """ Verify that when instantiating a Task with a uuid specified,
            it uses that uuid.
        """
        user = self.create_user()
        uuid = 'foobar'
        task = Task(description='my description', uuid=uuid, user=user)
        task.save()
        self.assertEqual(task.uuid, uuid)

    def test_create_task_undo(self):
        user = self.create_user()
        task = Task(description='foobar', user=user)
        task.save()
        self.assertEqual(len(Undo.objects.all()), 1)
        self.assertNotIn('old', Undo.serialize())
        self.assertEqual(len(Undo.serialize().splitlines()), 3)
        task.delete()
        #should we be clearing these somehow?
        #self.assertEqual(len(Undo.objects.all()), 0)

    def test_edit_task_undo(self):
        user = self.create_user()
        task = Task(description='foobar', user=user)
        task.save()
        task.annotate('annotation')
        self.assertEqual(len(Undo.objects.all()), 2)
        self.assertIn('old', Undo.serialize())
        # 'old' shouldn't have an annotation
        new_undo = Undo.objects.get(pk=2)
        self.assertNotIn('annotation_', new_undo.old)
        self.assertEqual(len(Undo.serialize().splitlines()), 7)
        self.assertNotIn('annotation_', Undo.serialize().splitlines()[4])

    def test_task_saving_without_data_change(self):
        """ Make sure that saving a task twice without
            a change in data doesn't create duplicate Undo's
        """
        user = self.create_user()
        task = Task(description='foobar', user=user)
        task.save()
        task.save()
        self.assertEqual(len(Undo.objects.all()), 1)

    def test_task_is_dirty(self):
        user = self.create_user()
        task = Task(description='foobar', user=user)
        self.assertItemsEqual(task._get_dirty_fields().keys(), ['user', 'description'])
        self.assertTrue(task._is_dirty())
        task.save()
        self.assertFalse(task._is_dirty())
        self.assertItemsEqual(task._get_dirty_fields().keys(), [])
        task.description = 'foobar2'
        self.assertItemsEqual(task._get_dirty_fields().keys(), ['description'])
        self.assertTrue(task._is_dirty())

    def test_task_is_dirty_foreign_key(self):
        user = self.create_user()
        task = Task(description='foobar', user=user)
        self.assertTrue(task._is_dirty())
        task.save()
        self.assertFalse(task._is_dirty())
        task.priority = Priority.objects.get(weight=1)
        self.assertItemsEqual(task._get_dirty_fields().keys(), ['priority'])
        self.assertTrue(task._is_dirty())

    def test_task_is_dirty_m2m(self):
        user = self.create_user()
        task = Task(description='foobar', user=user)
        self.assertTrue(task._is_dirty())
        task.save()
        self.assertFalse(task._is_dirty())
        task.tags.add(Tag.objects.create(tag='foobar'))
        self.assertItemsEqual(task._get_dirty_fields().keys(), ['tags'])
        self.assertTrue(task._is_dirty())

    def test_create_task_save_without_track(self):
        user = self.create_user()
        task = Task(description='foobar', user=user)
        task.save(track=False)
        self.assertEqual(len(Undo.objects.all()), 0)

    def test_mark_task_done(self):
        user = self.create_user()
        task = Task(description='test', user=user)
        task.save()
        self.assertEqual(task.status, 'pending')
        task.done()
        self.assertEqual(task.status, 'completed')

    def test_task_tags_empty(self):
        user = self.create_user()
        task = Task(description='foobar', user=user)
        task.save()
        self.assertEqual(list(task.tags.all()), [])

    def test_task_tags_single_tag(self):
        user = self.create_user()
        task = Task(description='foobar', user=user)
        task.save()

        # single tag
        tag = Tag.objects.create(tag='django')
        task.tags.add(tag)
        task.save()
        self.assertEqual(list(task.tags.all()), [tag])

    def test_task_tags_multiple_tags(self):
        user = self.create_user()
        task = Task(description='foobar', user=user)
        task.save()

        # multiple tags
        tag1 = Tag.objects.create(tag='spam')
        tag2 = Tag.objects.create(tag='eggs')
        task.tags.add(tag1, tag2)
        task.save()
        self.assertEqual(list(task.tags.all()), [tag1, tag2])

    def test_task_dependencies(self):
        user = self.create_user()
        task1 = Task.objects.create(description='task 1', user=user)
        task2 = Task.objects.create(description='task 2', user=user)
        task1.dependencies.add(task2)
        task1.save()

        self.assertEqual(list(task1.dependencies.all()), [task2])
        self.assertEqual(list(task2.task_set.all()), [task1])

    def test_task_todict(self):
        import time
        import datetime
        ts = time.time()
        dt = datetime.datetime.fromtimestamp(ts)
        expected = {
                    'uuid': '31ae59d3-7c9c-4418-ae8f-25ba123e072a',
                    'description': 'task description',
                    'project': 'test',
                    'priority': 'H',
                    'status': 'pending',
                    'tags': 'tag1,tag2',
                    'annotation_%s' % int(ts): u'annotation desc',
                    'entry': '12345',
                    }
        user = self.create_user()
        priority = Priority.objects.get(weight=3)
        project = Project.objects.create(name=expected['project'])
        task = Task.objects.create(description='task description',
                                   user=user,
                                   uuid=expected['uuid'],
                                   project=project,
                                   entry=datetime.datetime.fromtimestamp(int(expected['entry'])),
                                   priority=priority,
                                   )

        for tag in expected['tags'].split(','):
            task.add_tag(tag)
        task.annotate(expected['annotation_%s' % int(ts)], dt)

        self.assertEqual(task.todict(), expected)

    def test_task_fromdict(self):
        user = self.create_user()
        data = {'description': 'foobar', 'uuid': 'sssssssss',
                'status': 'pending',
                'entry': '12345',
                'user': user,
                'annotation_1324076995': u'this is an annotation',
                'priority': 'H',
                }
        task = Task.fromdict(data)

        # ensure the data is in the db, not just the task
        # object from above
        task = Task.objects.all()[0]
        self.assertEqual(list(Undo.objects.all()), [])
        data.pop('user')
        self.assertEqual(data, task.todict())

    def test_task_fromdict_track(self):
        user = self.create_user()
        data = {'description': 'foobar', 'uuid': 'sssssssss',
                'status': 'pending',
                'entry': '12345',
                'user': user,
                'annotation_1324076995': u'this is an annotation',
                'priority': 'H',
                }

        task = Task.fromdict(data, track=True)

        # ensure the data is in the db, not just the task
        # object from above
        task = Task.objects.all()[0]

        # see reasoning in the add_tasks_POST test
        self.assertEqual(Undo.objects.count(), 2)

        # this is a brand new task, the firts undo shouldn't
        # have an 'old' field.
        self.assertEqual(Undo.objects.all()[0].old, None)
        data.pop('user')
        self.assertEqual(data, task.todict())

        undo2 = Undo.objects.all()[1]
        self.assertNotEqual(undo2.old, undo2.new)

    def test_task_fromdict_priority_empty_string(self):
        user = self.create_user()
        data = {'description': 'foobar', 'uuid': 'sssssssss',
                'status': 'pending',
                'entry': '12345',
                'user': user,
                'annotation_1324076995': u'this is an annotation',
                'priority': '',
                }
        task = Task.fromdict(data)

        # ensure the data is in the db, not just the task
        # object from above
        task = Task.objects.all()[0]
        self.assertEqual(list(Undo.objects.all()), [])
        data.pop('user')
        data.pop('priority')
        self.assertEqual(data, task.todict())

    def test_task_fromdict_dependencies_dont_exist_yet(self):
        user = self.create_user()
        task1_info = {'description': 'foobar',
                      'uuid': '1234abc',
                      'entry': '1234',
                      'project': 'test',
                      'user': user,
                      'status': 'pending',
                      }

        task2_info = {'description': 'baz',
                      'uuid': 'aaaaaa',
                      'entry': '1237',
                      'depends': '1234abc',
                      'user': user,
                      'status': 'pending',
                      'annotation_123456': 'some note'
                      }

        task2 = Task.fromdict(task2_info)
        task1 = Task.fromdict(task1_info)

        task2_info.pop('user')
        task1_info.pop('user')
        self.assertEqual(task1.todict(), task1_info)
        self.assertEqual(task2.todict(), task2_info)

    def test_task_fromdict_dependencies(self):
        user = self.create_user()

        task1 = Task(user=user, description='test')
        task1.save(track=False)
        task2 = Task(user=user, description='test2')
        task2.save(track=False)

        data = {'description': 'foobar', 'uuid': 'sssssssss',
                'status': 'pending',
                'entry': '12345',
                'user': user,
                'annotation_1324076995': u'this is an annotation',
                'depends': u','.join([t.uuid for t in (task1, task2)]),
                'priority': '',
                }

        task = Task.fromdict(data)

        # ensure the data is in the db, not just the task
        # object from above
        task = Task.objects.get(description='foobar')
        self.assertEqual(list(Undo.objects.all()), [])
        data.pop('user')
        data.pop('priority')
        self.assertEqual(data, task.todict())

    def test_task_fromdict_unicode(self):
        user = self.create_user()
        data = {'description': u'foobar', 'uuid': u'sssssssss',
                'status': u'pending',
                'entry': u'12345',
                'user': user,
                'annotation_1324076995': u'this is an annotation',
                'priority': u'H',
                }

        task = Task.fromdict(data)

        self.assertEqual(Task.objects.count(), 1)
        # ensure the data is in the db, not just the task
        # object from above
        task = Task.objects.all()[0]

        self.assertEqual(list(Undo.objects.all()), [])
        data.pop('user')
        self.assertEqual(data, task.todict())

    def test_task_fromdict_optional_due(self):
        user = self.create_user()
        data = {'description': 'foobar', 'uuid': 'sssssssss',
                'status': 'pending',
                'entry': '12345',
                'due': '45678',
                'user': user,
                'annotation_1324076995': 'this is an annotation',
                }
        task = Task.fromdict(data)
        self.assertEqual(list(Undo.objects.all()), [])
        data.pop('user')
        self.assertEqual(data, task.todict())

    def test_task_fromdict_optional_end(self):
        user = self.create_user()
        data = {'description': 'foobar', 'uuid': 'sssssssss',
                'status': 'completed',
                'entry': '12345',
                'end': '45678',
                'user': user,
                'annotation_1324076995': 'this is an annotation',
                }
        task = Task.fromdict(data)
        self.assertEqual(list(Undo.objects.all()), [])
        data.pop('user')
        self.assertEqual(data, task.todict())


class TestViews(TaskTestCase):
    def test_pending_tasks(self):
        user = self.create_user()
        task = Task(description='test, test', user=user)
        task.save()
        self.assertEqual(len(Task.objects.all()), 1)

        response = self.client.get('/pending/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['datagrid'].rows), 1)

    def test_completed_tasks(self):
        response = self.client.get('/completed/')
        self.assertEqual(response.status_code, 200)

    def test_add_task_GET(self):
        self._create_user_and_login()
        response = self.client.get('/add/task/')
        self.assertEqual(response.status_code, 200)

    def test_add_tasks_GET_no_login(self):
        response = self.client.get('/add/task/')
        # should redirect ot login screen
        self.assertRedirects(response, '/accounts/login/?next=/add/task/')

    def test_add_tasks_POST(self):
        self._create_user_and_login()
        Tag.objects.create(tag='tag1')
        post_data = {'description': 'foobar',
                     'priority': '',
                     'user': '1',
                     'tags': ['1'],
                     'status': 'pending'
                    }
        self.assertEqual(len(Task.objects.all()), 0)
        response = self.client.post('/add/task/', post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(Task.objects.all()), 1)
        task = Task.objects.all()[0]
        taskdict = task.todict()
        # uuid and entry are auto-generated, don't
        # compare with them
        taskdict.pop('uuid')
        taskdict.pop('entry')
        post_data.pop('user')
        post_data.pop('priority')
        post_data.update({'tags': 'tag1'})
        self.assertEqual(post_data, taskdict)

        # 2 undo objects: 1 for adding task, 1 for adding
        # relations (tags, priority, etc...
        # I'd rather have 1, but this is easier
        self.assertEqual(Undo.objects.count(), 2)
        self.assertEqual(Undo.objects.all()[0].old, None)
        self.assertNotEqual(Undo.objects.all()[1].new, None)

    def test_add_tasks_POST_no_login(self):
        pass

    def test_taskdb_GET_pending(self):
        self._create_user_and_login()
        response = self.client.get('/taskdb/pending.data')
        self.assertEqual(response.status_code, 200)

    def test_taskdb_GET_completed(self):
        self._create_user_and_login()
        response = self.client.get('/taskdb/completed.data')
        self.assertEqual(response.status_code, 200)

    def test_taskdb_GET_undo(self):
        self._create_user_and_login()
        response = self.client.get('/taskdb/undo.data')
        self.assertEqual(response.status_code, 200)

    def test_taskdb_POST(self):
        self._create_user_and_login()

    def test_taskdb_PUT_pending(self):
        self._create_user_and_login()
        data = open(os.path.expanduser('~/.task/pending.data'), 'r').read()
        response = self.client.put('/taskdb/pending.data',
                        content_type='text/plain',
                        data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(Undo.objects.all()), [])
        self.assertEqual(Task.serialize('pending'), data)

    def test_taskdb_PUT_completed(self):
        self._create_user_and_login()
        data = open(os.path.expanduser('~/.task/completed.data'), 'r').read()
        response = self.client.put('/taskdb/completed.data',
                        content_type='text/plain',
                        data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(Undo.objects.all()), [])
        self.assertEqual(Task.serialize('completed'), data)

    def test_taskdb_PUT_undo(self):
        self._create_user_and_login()
        data = open(os.path.expanduser('~/.task/undo.data'), 'r').read()
        expected_parsed = parse_undo(data)

        post_response = self.client.put('/taskdb/undo.data',
                        content_type='text/plain',
                        data=data)
        self.assertEqual(post_response.status_code, 200)

        get_response = self.client.get('/taskdb/undo.data')

        actual_parsed = parse_undo(get_response.content)
        self.assertEqual(expected_parsed, actual_parsed)

    def test_taskdb_PUT_all(self):
        self._create_user_and_login()
        for fname in ['pending', 'undo', 'completed']:
            path = os.path.expanduser('~/.task/%s.data' % fname)
            data = open(path, 'r').read()
            response = self.client.put('/taskdb/%s.data' % fname,
                        content_type='text/plain',
                        data=data)
            self.assertEqual(response.status_code, 200)

    def test_taskdb_PUT_twice(self):
        """ I hit a bug where tasks weren't cleared properly. This tests it.
        """
        for x in range(2):
            self.test_taskdb_PUT_all()

    def test_parse_undo(self):
        parsed = parse_undo(UNDO_SAMPLE)
        self.assertEqual(parsed, PARSED_UNDO_SAMPLE)

    def _create_user_and_login(self):
        user = self.create_user('foo', 'bar')
        self.assertTrue(user.check_password('bar'))
        success = self.client.login(username='foo', password='bar')
        self.assertTrue(success)

    def test_add_project_POST(self):
        self._create_user_and_login()
        data = {'name': 'taskweb'}
        response = self.client.post('/add/project/', data)
        self.assertEqual(response.status_code, 200)

    def test_add_tag_POST(self):
        self._create_user_and_login()
        data = {'tag': u'tag1'}
        response = self.client.post('/add/tags/', data)
        self.assertEqual(response.status_code, 200)
        tags = Tag.objects.all()
        self.assertEqual(len(tags), 1)
        tag = tags[0]
        self.assertEqual(tag.tag, u'tag1')


PARSED_UNDO_SAMPLE = [
    {'time': '1326338657',
      'new': '[description:"note: this is a task\&dquot;" entry:"1326338657" status:"pending" uuid:"6f34e415-2441-4058-8c11-320f5c2b2792"]\n'
      },
    {'time': '1326338708',
      'old': '[description:"foo \&dquot;bar\&dquot;" entry:"1326250353" status:"pending" uuid:"4300e85d-9bbc-49a6-ba89-89f024bc0795"]\n',
      'new': '[description:"foo \&dquot;bar\&dquot;" end:"1326338705" entry:"1326250353" status:"deleted" uuid:"4300e85d-9bbc-49a6-ba89-89f024bc0795"]\n'
      }]

UNDO_SAMPLE =\
"""
time 1326338657
new [description:"note: this is a task\&dquot;" entry:"1326338657" status:"pending" uuid:"6f34e415-2441-4058-8c11-320f5c2b2792"]
---
time 1326338708
old [description:"foo \&dquot;bar\&dquot;" entry:"1326250353" status:"pending" uuid:"4300e85d-9bbc-49a6-ba89-89f024bc0795"]
new [description:"foo \&dquot;bar\&dquot;" end:"1326338705" entry:"1326250353" status:"deleted" uuid:"4300e85d-9bbc-49a6-ba89-89f024bc0795"]
"""
