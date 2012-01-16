from django.test import TestCase
from django.contrib.auth.models import User

from task.models import Task


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

    def test_mark_task_done(self):
        user = self.create_user()
        task = Task(description='test', user=user)
        task.save()
        self.assertEqual(task.status, 'pending')
        task.done()
        self.assertEqual(task.status, 'completed')

    def test_task_tags(self):
        user = self.create_user()
        task = Task(description='foobar', user=user)
        task.save()
        self.assertEqual(task.tags, '')

        # single tag
        task.tags = ['django']
        task.save()
        self.assertEqual(task.tags, ['django'])

        # multiple tags
        task.tags = ['spam', 'eggs']
        task.save()
        self.assertEqual(task.tags, ['spam', 'eggs'])

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
                                   tags=expected['tags'].split(','),
                                   entry=datetime.datetime.fromtimestamp(int(expected['entry'])),
                                   )

        task.annotate(expected['annotation_%s' % int(ts)], dt)

        self.assertEqual(task.todict(), expected)


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

    def test_taskdb_GET(self):
        self._create_user_and_login()
        response = self.client.get('/taskdb/pending.data')
        self.assertEqual(response.status_code, 200)

    def test_taskdb_POST(self):
        self._create_user_and_login()

    def test_taskdb_PUT(self):
        self._create_user_and_login()

    def create_user(self, username='foo', passw='baz'):
        user = User.objects.create_user(username, 'foo@test.com', passw)
        user.save()
        return user

    def _create_user_and_login(self):
        user = self.create_user('foo', 'bar')
        self.assertTrue(user.check_password('bar'))
        success = self.client.login(username='foo', password='bar')
        self.assertTrue(success)
