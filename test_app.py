import unittest
from datetime import date, timedelta
import db
import app

class TaskManagerTestCase(unittest.TestCase):
    def setUp(self):
        self.flask_app = app.create_app()
        self.flask_app.config['TESTING'] = True
        self.client = self.flask_app.test_client()

        with self.flask_app.app_context():
            db.init_db()
            db.seed_sample_data_if_empty()

    def test_dashboard_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'TaskFlow', response.data)
        self.assertIn(b'Total Tasks', response.data)
        self.assertIn(b'Pending Tasks', response.data)
        self.assertIn(b'Completed', response.data)
        self.assertIn(b'Category: All', response.data)

    def test_create_task_with_category(self):
        future_date = (date.today() + timedelta(days=5)).isoformat()
        response = self.client.post('/tasks/create', data={
            'title': 'Finance Budgeting Task',
            'description': 'Review monthly savings and investments',
            'category': 'Finance',
            'due_date': future_date,
            'priority': 'High'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Finance Budgeting Task', response.data)
        self.assertIn(b'Finance', response.data)
        self.assertIn(b'Task added successfully!', response.data)

    def test_create_task_validation_empty_title(self):
        response = self.client.post('/tasks/create', data={
            'title': '   ',
            'description': 'No title',
            'priority': 'Low'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Task title is required!', response.data)

    def test_create_task_validation_title_too_long(self):
        long_title = 'A' * 151
        response = self.client.post('/tasks/create', data={
            'title': long_title,
            'description': 'Valid description',
            'priority': 'Medium'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Task title must not exceed 150 characters.', response.data)

    def test_create_task_validation_past_due_date(self):
        past_date = (date.today() - timedelta(days=2)).isoformat()
        response = self.client.post('/tasks/create', data={
            'title': 'Past Date Task',
            'due_date': past_date,
            'priority': 'Medium'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Due date must be today or a future date!', response.data)

    def test_edit_task_with_category(self):
        with self.flask_app.app_context():
            conn = db.get_db()
            task = conn.execute("SELECT id FROM tasks LIMIT 1").fetchone()
            task_id = task['id']

        future_date = (date.today() + timedelta(days=10)).isoformat()
        response = self.client.post(f'/tasks/{task_id}/edit', data={
            'title': 'Updated With Category',
            'description': 'Updated Description',
            'category': 'Health',
            'due_date': future_date,
            'priority': 'Low',
            'status': 'Completed'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Updated With Category', response.data)
        self.assertIn(b'Health', response.data)

    def test_inline_update_description(self):
        with self.flask_app.app_context():
            conn = db.get_db()
            task = conn.execute("SELECT id FROM tasks LIMIT 1").fetchone()
            task_id = task['id']

        # AJAX inline update description
        response = self.client.post(
            f'/tasks/{task_id}/update-description',
            data={'description': 'Freshly edited inline description!'},
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['description'], 'Freshly edited inline description!')

        # Verify in DB
        with self.flask_app.app_context():
            conn = db.get_db()
            updated = conn.execute("SELECT description FROM tasks WHERE id = ?", (task_id,)).fetchone()
            self.assertEqual(updated['description'], 'Freshly edited inline description!')

    def test_inline_update_due_date_future(self):
        with self.flask_app.app_context():
            conn = db.get_db()
            task = conn.execute("SELECT id FROM tasks LIMIT 1").fetchone()
            task_id = task['id']

        future_date = (date.today() + timedelta(days=7)).isoformat()
        response = self.client.post(
            f'/tasks/{task_id}/update-due-date',
            data={'due_date': future_date},
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['due_date'], future_date)

    def test_inline_update_due_date_reject_past(self):
        with self.flask_app.app_context():
            conn = db.get_db()
            task = conn.execute("SELECT id FROM tasks LIMIT 1").fetchone()
            task_id = task['id']

        past_date = (date.today() - timedelta(days=3)).isoformat()
        response = self.client.post(
            f'/tasks/{task_id}/update-due-date',
            data={'due_date': past_date},
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data['success'])
        self.assertIn('Due date must be today or a future date!', data['error'])

    def test_toggle_task_ajax(self):
        with self.flask_app.app_context():
            conn = db.get_db()
            task = conn.execute("SELECT id, status FROM tasks LIMIT 1").fetchone()
            task_id = task['id']
            initial_status = task['status']

        response = self.client.post(
            f'/tasks/{task_id}/toggle',
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        expected = 'Completed' if initial_status == 'Pending' else 'Pending'
        self.assertEqual(data['new_status'], expected)

    def test_delete_task(self):
        with self.flask_app.app_context():
            conn = db.get_db()
            cursor = conn.execute("INSERT INTO tasks (title, status) VALUES ('To Delete', 'Pending')")
            conn.commit()
            task_id = cursor.lastrowid

        response = self.client.post(f'/tasks/{task_id}/delete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'To Delete', response.data)
        self.assertIn(b'Task deleted successfully!', response.data)

    def test_api_single_task(self):
        with self.flask_app.app_context():
            conn = db.get_db()
            task = conn.execute("SELECT id, title, category FROM tasks LIMIT 1").fetchone()
            task_id = task['id']
            expected_title = task['title']
            expected_category = task['category']

        response = self.client.get(f'/api/tasks/{task_id}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['id'], task_id)
        self.assertEqual(data['title'], expected_title)
        self.assertEqual(data['category'], expected_category)

if __name__ == '__main__':
    unittest.main()
