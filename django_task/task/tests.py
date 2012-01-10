from django.test import TestCase
from django.contrib.auth.models import User

from task.models import Task


class TestModels(TestCase):
    def test_create_task_no_uuid(self):
        """ Verify that a `Task`s uuid field is automatically populated
            when not specified.
        """
        # description is the only required field
        task = Task(description='foobar')
        task.save()
        self.assertTrue(hasattr(task, 'uuid'))
        self.assertNotEqual(task.uuid, None)

    def test_create_task_with_uuid(self):
        """ Verify that when instantiating a Task with a uuid specified,
            it uses that uuid.
        """
        uuid = 'foobar'
        task = Task(description='my description', uuid=uuid)
        task.save()
        self.assertEqual(task.uuid, uuid)

    def test_mark_task_done(self):
        pass


class TestViews(TestCase):
    def test_pending_tasks(self):
        response = self.client.get('/pending/')
        self.assertEqual(response.status_code, 200)

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

    def _create_user_and_login(self):
        user = User.objects.create_user('foo', 'foo@test.com', 'bar')
        user.save()
        self.assertTrue(user.check_password('bar'))
        success = self.client.login(username='foo', password='bar')
        self.assertTrue(success)
