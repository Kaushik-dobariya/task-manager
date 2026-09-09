import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import db

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-task-manager-secret-key-2026')
    
    # Initialize database connection hooks and seed data
    db.init_app(app)

    from datetime import date

    @app.template_filter('format_date')
    def format_date(val):
        if not val:
            return 'Recently'
        if hasattr(val, 'strftime'):
            return val.strftime('%Y-%m-%d')
        return str(val)[:10]

    @app.route('/')
    def index():
        conn = db.get_db()

        # Calculate metrics for dashboard cards
        total_tasks = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        pending_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Pending'").fetchone()[0]
        completed_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Completed'").fetchone()[0]

        # Optional backend filtering (also complemented by real-time frontend search/filter)
        status_filter = request.args.get('status', 'All')
        search_query = request.args.get('q', '').strip()
        priority_filter = request.args.get('priority', 'All')
        category_filter = request.args.get('category', 'All')

        sql = "SELECT * FROM tasks WHERE 1=1"
        params = []

        if status_filter in ('Pending', 'Completed'):
            sql += " AND status = ?"
            params.append(status_filter)

        if priority_filter in ('Low', 'Medium', 'High'):
            sql += " AND priority = ?"
            params.append(priority_filter)

        if category_filter and category_filter != 'All':
            sql += " AND category = ?"
            params.append(category_filter)

        if search_query:
            sql += " AND (title LIKE ? OR description LIKE ?)"
            wildcard = f"%{search_query}%"
            params.extend([wildcard, wildcard])

        # Order by status (Pending first), then priority/due_date, then created_at descending
        sql += """
            ORDER BY 
                CASE status WHEN 'Pending' THEN 1 ELSE 2 END,
                CASE 
                    WHEN due_date IS NOT NULL AND due_date != '' THEN due_date 
                    ELSE '9999-12-31' 
                END ASC,
                id DESC
        """

        tasks = conn.execute(sql, params).fetchall()

        # Collect distinct categories used in tasks
        db_categories = [r[0] for r in conn.execute("SELECT DISTINCT category FROM tasks WHERE category IS NOT NULL AND category != ''").fetchall()]
        standard_categories = ['Work', 'Personal', 'Study', 'Finance', 'Health', 'General']
        # Merge preserving order
        all_categories = list(dict.fromkeys(standard_categories + db_categories))

        return render_template(
            'index.html',
            tasks=tasks,
            total_tasks=total_tasks,
            pending_tasks=pending_tasks,
            completed_tasks=completed_tasks,
            active_status=status_filter,
            active_search=search_query,
            active_priority=priority_filter,
            active_category=category_filter,
            categories=all_categories,
            today=date.today().isoformat()
        )

    from datetime import datetime, date

    @app.route('/tasks/create', methods=['POST'])
    def create_task():
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        due_date = request.form.get('due_date', '').strip()
        priority = request.form.get('priority', 'Medium').strip()
        category = request.form.get('category', 'General').strip() or 'General'

        # Validation: Title required
        if not title:
            flash('Task title is required!', 'danger')
            return redirect(url_for('index'))

        # Validation: Title length
        if len(title) > 150:
            flash('Task title must not exceed 150 characters.', 'danger')
            return redirect(url_for('index'))

        # Validation: Description length
        if len(description) > 1000:
            flash('Task description must not exceed 1000 characters.', 'danger')
            return redirect(url_for('index'))

        # Validation: Category length
        if len(category) > 50:
            category = category[:50]

        # Validation: Priority check
        if priority not in ('Low', 'Medium', 'High'):
            flash('Invalid priority selected. Defaulted to Medium.', 'warning')
            priority = 'Medium'

        # Validation: Due date format (YYYY-MM-DD) & future date constraint
        if due_date:
            try:
                parsed_date = datetime.strptime(due_date, '%Y-%m-%d').date()
                if parsed_date < date.today():
                    flash('Due date must be today or a future date!', 'danger')
                    return redirect(url_for('index'))
            except ValueError:
                flash('Invalid due date format. Please use YYYY-MM-DD.', 'danger')
                return redirect(url_for('index'))
        else:
            due_date = None

        conn = db.get_db()
        conn.execute(
            """
            INSERT INTO tasks (title, description, category, due_date, priority, status)
            VALUES (?, ?, ?, ?, ?, 'Pending')
            """,
            (title, description, category, due_date, priority)
        )
        conn.commit()
        flash('Task added successfully! 🎉', 'success')
        return redirect(url_for('index'))

    @app.route('/tasks/<int:task_id>/edit', methods=['POST'])
    def edit_task(task_id):
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        due_date = request.form.get('due_date', '').strip()
        priority = request.form.get('priority', 'Medium').strip()
        status = request.form.get('status', 'Pending').strip()
        category = request.form.get('category', 'General').strip() or 'General'

        # Validation: Title required
        if not title:
            flash('Task title cannot be empty!', 'danger')
            return redirect(url_for('index'))

        # Validation: Title length
        if len(title) > 150:
            flash('Task title must not exceed 150 characters.', 'danger')
            return redirect(url_for('index'))

        # Validation: Description length
        if len(description) > 1000:
            flash('Task description must not exceed 1000 characters.', 'danger')
            return redirect(url_for('index'))

        # Validation: Category length
        if len(category) > 50:
            category = category[:50]

        # Validation: Priority check
        if priority not in ('Low', 'Medium', 'High'):
            flash('Invalid priority selected. Defaulted to Medium.', 'warning')
            priority = 'Medium'

        # Validation: Status check
        if status not in ('Pending', 'Completed'):
            flash('Invalid status selected. Defaulted to Pending.', 'warning')
            status = 'Pending'

        # Validation: Due date format
        if due_date:
            try:
                datetime.strptime(due_date, '%Y-%m-%d')
            except ValueError:
                flash('Invalid due date format. Please use YYYY-MM-DD.', 'danger')
                return redirect(url_for('index'))
        else:
            due_date = None

        conn = db.get_db()
        cursor = conn.execute(
            """
            UPDATE tasks
            SET title = ?, description = ?, category = ?, due_date = ?, priority = ?, status = ?
            WHERE id = ?
            """,
            (title, description, category, due_date, priority, status, task_id)
        )
        conn.commit()

        if cursor.rowcount == 0:
            flash('Task not found.', 'warning')
        else:
            flash('Task updated successfully! ✨', 'success')

        return redirect(url_for('index'))

    @app.route('/tasks/<int:task_id>/update-description', methods=['POST'])
    def update_task_description(task_id):
        """Quick inline update for task description from the task list."""
        description = request.form.get('description', '').strip()

        if len(description) > 1000:
            msg = 'Description must not exceed 1000 characters.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': msg}), 400
            flash(msg, 'danger')
            return redirect(url_for('index'))

        conn = db.get_db()
        cursor = conn.execute(
            "UPDATE tasks SET description = ? WHERE id = ?",
            (description, task_id)
        )
        conn.commit()

        if cursor.rowcount == 0:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': 'Task not found'}), 404
            flash('Task not found.', 'warning')
            return redirect(url_for('index'))

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'description': description})

        flash('Description updated successfully! 📝', 'success')
        return redirect(url_for('index'))

    @app.route('/tasks/<int:task_id>/update-due-date', methods=['POST'])
    def update_task_due_date(task_id):
        """Quick inline update for task due date (future date including today only)."""
        due_date = request.form.get('due_date', '').strip()

        if due_date:
            try:
                parsed_date = datetime.strptime(due_date, '%Y-%m-%d').date()
                if parsed_date < date.today():
                    msg = 'Due date must be today or a future date!'
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({'success': False, 'error': msg}), 400
                    flash(msg, 'danger')
                    return redirect(url_for('index'))
            except ValueError:
                msg = 'Invalid date format. Please use YYYY-MM-DD.'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'error': msg}), 400
                flash(msg, 'danger')
                return redirect(url_for('index'))
        else:
            due_date = None

        conn = db.get_db()
        cursor = conn.execute(
            "UPDATE tasks SET due_date = ? WHERE id = ?",
            (due_date, task_id)
        )
        conn.commit()

        if cursor.rowcount == 0:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': 'Task not found'}), 404
            flash('Task not found.', 'warning')
            return redirect(url_for('index'))

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'due_date': due_date or ''})

        flash('Due date updated! 📅', 'success')
        return redirect(url_for('index'))

    @app.route('/tasks/<int:task_id>/toggle', methods=['POST'])
    def toggle_task(task_id):
        conn = db.get_db()
        task = conn.execute("SELECT status FROM tasks WHERE id = ?", (task_id,)).fetchone()

        if not task:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': 'Task not found'}), 404
            flash('Task not found.', 'warning')
            return redirect(url_for('index'))

        new_status = 'Completed' if task['status'] == 'Pending' else 'Pending'
        conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
        conn.commit()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Also calculate updated counts
            total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
            pending = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Pending'").fetchone()[0]
            completed = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Completed'").fetchone()[0]
            return jsonify({
                'success': True,
                'new_status': new_status,
                'total_tasks': total,
                'pending_tasks': pending,
                'completed_tasks': completed
            })

        msg = 'Task marked as Completed! ✅' if new_status == 'Completed' else 'Task marked as Pending ⏳'
        flash(msg, 'info')
        return redirect(url_for('index'))

    @app.route('/tasks/<int:task_id>/delete', methods=['POST'])
    def delete_task(task_id):
        conn = db.get_db()
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()

        if cursor.rowcount == 0:
            flash('Task not found.', 'warning')
        else:
            flash('Task deleted successfully! 🗑️', 'secondary')

        return redirect(url_for('index'))

    @app.route('/api/tasks/<int:task_id>')
    def get_task_json(task_id):
        """API endpoint to retrieve single task details as JSON for the edit modal."""
        conn = db.get_db()
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        return jsonify({
            'id': task['id'],
            'title': task['title'],
            'description': task['description'] or '',
            'category': task['category'] or 'General',
            'due_date': task['due_date'] or '',
            'priority': task['priority'],
            'status': task['status'],
            'created_at': str(task['created_at'])
        })

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
