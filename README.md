# 📋 TaskFlow - Personal Task Manager

A clean, responsive, beginner-friendly Personal Task Manager web application built with **Python (Flask)**, **SQLite**, **Bootstrap 5**, and **Vanilla JavaScript**.

---

## 🚀 Features

- **Dashboard**:
  - Summary metric cards for **Total Tasks**, **Pending Tasks**, and **Completed Tasks**.
- **Task Management (Full CRUD)**:
  - **Create**: Add tasks with Title, Description, Due Date, and Priority.
  - **Read**: View task cards with priority badges, overdue indicators, and creation dates.
  - **Update**: Edit any task details via a modal without navigating away.
  - **Delete**: Safe delete with confirmation dialog.
  - **Quick Toggle**: Instantly mark tasks as Completed or Pending with one click.
- **Search & Filters**:
  - **Live Search**: Instant real-time filtering as you type into the search box.
  - **Status Filter**: Switch between *All*, *Pending*, and *Completed* tabs.
  - **Priority Filter**: Filter tasks by *High*, *Medium*, or *Low*.
- **Modern UI & Aesthetics**:
  - **Light & Dark Mode**: Seamless toggle with persistence in browser `localStorage`.
  - Responsive design that looks great on mobile, tablet, and desktop.
  - Built with Bootstrap 5.3 and Google Fonts (Inter).

---

## 📂 Project Architecture

```text
task-manager/
├── app.py               # Main Flask application with routes and controllers
├── db.py                # Database connection helper, teardown, and seed data
├── schema.sql           # SQLite table schema definition
├── requirements.txt     # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css    # Custom CSS & theme styling
│   └── js/
│       └── main.js      # Vanilla JS (Theme switch, live search, modals)
└── templates/
    ├── base.html        # Shared base template with navbar & CDN links
    └── index.html       # Dashboard with metric cards, filters, and modals
```

---

## 🛠️ How to Run the Application

### 1. Activate the Virtual Environment

On Windows (PowerShell):
```powershell
.\venv\Scripts\Activate.ps1
```

*(If virtual environment is not yet created, run `python -m venv venv` and `.\venv\Scripts\pip install -r requirements.txt`)*

### 2. Run the Flask App

```powershell
.\venv\Scripts\python.exe app.py
```

### 3. Open in Browser

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 💡 How It Works (For Beginners)

1. **`schema.sql`**: Tells SQLite what a task looks like (table columns, data types, constraints).
2. **`db.py`**: Connects to the SQLite database file (`tasks.db`) and handles closing the connection when each web request finishes.
3. **`app.py`**:
   - Handles HTTP routes (`/`, `/tasks/create`, `/tasks/<id>/edit`, `/tasks/<id>/delete`, `/tasks/<id>/toggle`).
   - Fetches data from SQLite and passes it to the HTML templates.
4. **`templates/`**:
   - `base.html` defines the layout shared by all pages.
   - `index.html` uses Jinja2 template tags (`{{ task.title }}`, `{% for task in tasks %}`) to generate dynamic HTML from the database.
5. **`static/`**:
   - `style.css` adds visual polish, animations, and dark mode tweaks.
   - `main.js` provides instant search, filter tabs, modal popups, and light/dark mode memory.
