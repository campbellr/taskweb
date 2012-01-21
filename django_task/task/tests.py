import os

from django.test import TestCase
from django.utils import unittest
from django.contrib.auth.models import User

from task.models import Task, Tag, Undo
from task.util import parse_undo
from task.grids import IDColumn


class TestGrids(TestCase):
    def create_user(self, username='foo', passw='baz'):
        user = User.objects.create_user(username, 'foo@test.com', passw)
        user.save()
        return user

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


class TestTaskModel(TestCase):
    def create_user(self, username='foo', passw='baz'):
        user = User.objects.create_user(username, 'foo@test.com', passw)
        user.save()
        return user

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
                    'status': 'pending',
                    'tags': 'tag1,tag2',
                    'annotation_%s' % int(ts): u'annotation desc',
                    'entry': '12345',
                    }
        user = self.create_user()
        task = Task.objects.create(description='task description',
                                   user=user,
                                   uuid=expected['uuid'],
                                   project=expected['project'],
                                   entry=datetime.datetime.fromtimestamp(int(expected['entry'])),
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
                'annotation_1324076995': 'this is an annotation',
                }
        task = Task.fromdict(data)
        self.assertEqual(list(Undo.objects.all()), [])
        data.pop('user')
        self.assertEqual(data, task.todict())


class TestViews(TestCase):
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
        response = self.client.get('/add/')
        self.assertEqual(response.status_code, 200)

    def test_add_tasks_GET_no_login(self):
        response = self.client.get('/add/')
        # should redirect ot login screen
        self.assertRedirects(response, '/accounts/login/?next=/add/')

    def test_add_tasks_POST(self):
        pass

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

    def test_taskdb_PUT_completed(self):
        self._create_user_and_login()
        data = open(os.path.expanduser('~/.task/completed.data'), 'r').read()
        response = self.client.put('/taskdb/completed.data',
                        content_type='text/plain',
                        data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(Undo.objects.all()), [])

    def test_taskdb_PUT_undo(self):
        self._create_user_and_login()
        data = open(os.path.expanduser('~/.task/undo.data'), 'r').read()
        response = self.client.put('/taskdb/undo.data',
                        content_type='text/plain',
                        data=data)
        self.assertEqual(response.status_code, 200)

        # this doesn't work, maybe use ordereddict?
        #expected = data.split('---')
        #actual = Undo.serialize().split('---')
        #self.assertEqual(len(expected), len(actual))

        #for i in range(len(expected)):
        #    self.assertEqual(expected[i], actual[i])

    def test_taskdb_PUT_all(self):
        self._create_user_and_login()
        for fname in ['pending', 'undo', 'completed']:
            data = open(os.path.expanduser('~/.task/%s.data' % fname), 'r').read()
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

    def create_user(self, username='foo', passw='baz'):
        users = User.objects.filter(username=username)
        if users:
            return users[0]

        user = User.objects.create_user(username, 'foo@test.com', passw)
        user.save()
        return user

    def _create_user_and_login(self):
        user = self.create_user('foo', 'bar')
        self.assertTrue(user.check_password('bar'))
        success = self.client.login(username='foo', password='bar')
        self.assertTrue(success)


PARSED_UNDO_SAMPLE = [
    {'time': '1326338657',
      'new': '[description:"note: this is a task\&dquot;" entry:"1326338657" status:"pending" uuid:"6f34e415-2441-4058-8c11-320f5c2b2792"]'
      },
    {'time': '1326338708',
      'old': '[description:"foo \&dquot;bar\&dquot;" entry:"1326250353" status:"pending" uuid:"4300e85d-9bbc-49a6-ba89-89f024bc0795"]',
      'new': '[description:"foo \&dquot;bar\&dquot;" end:"1326338705" entry:"1326250353" status:"deleted" uuid:"4300e85d-9bbc-49a6-ba89-89f024bc0795"]'
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
