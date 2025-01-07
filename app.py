# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime , timedelta
import csv
import os
import sys
import threading
import uuid
import webview 

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# Modify Flask app initialization
app = Flask(__name__,
           template_folder=resource_path('templates'),
           static_folder=resource_path('static'))

# CSV file setup
TASKS_FILE = 'tasks.csv'
FIELDNAMES = ['id', 'title', 'start_time', 'completion_time', 'time_taken', 'importance', 'status', 'created_at']


def get_analytics_data(time_filter='all'):
    tasks = get_tasks()
    now = datetime.now()
    
    if time_filter == '24h':
        cutoff = now - timedelta(days=1)
    elif time_filter == '7d':
        cutoff = now - timedelta(days=7)
    elif time_filter == '30d':
        cutoff = now - timedelta(days=30)
    else:
        cutoff = datetime.min
    
    # Convert string dates to datetime objects for comparison
    filtered_tasks = []
    for task in tasks:
        try:
            task_date = datetime.strptime(task['created_at'], '%Y-%m-%d %H:%M')
            if task_date >= cutoff:
                filtered_tasks.append(task)
        except (ValueError, TypeError):
            continue

    # Calculate analytics
    total_tasks = len(filtered_tasks)
    completed_tasks = len([t for t in filtered_tasks if t['status'] == 'completed'])
    pending_tasks = total_tasks - completed_tasks
    
    # Priority distribution
    priority_dist = {
        'high': len([t for t in filtered_tasks if t['importance'] == 'high']),
        'medium': len([t for t in filtered_tasks if t['importance'] == 'medium']),
        'low': len([t for t in filtered_tasks if t['importance'] == 'low'])
    }
    # print(filtered_tasks)  # Check if tasks are being filtered correctly.
     
    
    # Average completion time
    completion_times = []
    for task in filtered_tasks:
        if task['status'] == 'completed' and task['time_taken']:
            try:
                hours = float(task['time_taken'].split()[0])
                completion_times.append(hours)
            except (ValueError, IndexError):
                continue
    
    avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
    
    return {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'priority_distribution': priority_dist,
        'avg_completion_time': round(avg_completion_time, 2)
    }

@app.route('/get_analytics')
def get_analytics():
    time_filter = request.args.get('time_filter', 'all')
    return jsonify(get_analytics_data(time_filter))




@app.route('/analytics')
def analytics():
    analytics_data = get_analytics_data()
    return render_template('analytics.html', analytics=analytics_data)

@app.route('/api/analytics')
def get_analytics_api():
    time_filter = request.args.get('time_filter', 'all')
    return jsonify(get_analytics_data(time_filter))


def init_csv():
    if not os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writeheader()

def get_tasks():
    tasks = []
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, 'r', newline='') as file:
            reader = csv.DictReader(file)
            tasks = list(reader)
    return tasks

def save_task(task_data):
    tasks = get_tasks()
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    task = {
        'id': str(uuid.uuid4()),
        'title': task_data['title'],
        'start_time': current_time,  # Automatically set start time to current time
        'completion_time': '',
        'time_taken': '',
        'importance': task_data['importance'],
        'status': 'pending',
        'created_at': current_time
    }
    tasks.append(task)
    
    with open(TASKS_FILE, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(tasks)
    return task

def update_task_completion(task_id):
    tasks = get_tasks()
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    for task in tasks:
        if task['id'] == task_id:
            task['status'] = 'completed'
            task['completion_time'] = current_time
            
            # Calculate time taken
            try:
                if task['start_time']:  # Ensure start_time is not empty
                    start_time = datetime.strptime(task['start_time'], '%Y-%m-%d %H:%M')
                    end_time = datetime.strptime(current_time, '%Y-%m-%d %H:%M')
                    time_diff = end_time - start_time
                    hours = time_diff.total_seconds() / 3600
                    task['time_taken'] = f"{hours:.2f} hours"
                else:
                    task['time_taken'] = 'Start time missing'
            except ValueError as e:
                print(f"Error parsing dates: {e}")  # Log the error for debugging
                task['time_taken'] = 'Time calculation error'
    
    with open(TASKS_FILE, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(tasks)


def delete_task_by_id(task_id):
    tasks = get_tasks()
    tasks = [task for task in tasks if task['id'] != task_id]
    
    with open(TASKS_FILE, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(tasks)

@app.route('/')
def index():
    search_query = request.args.get('search', '').lower()
    tasks = get_tasks()
    
    if search_query:
        tasks = [task for task in tasks if search_query in task['title'].lower()]
    
    # Sort tasks by created_at in reverse order
    tasks.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render_template('index.html', tasks=tasks, search_query=search_query)

@app.route('/add_task', methods=['POST'])
def add_task():
    task_data = {
        'title': request.form.get('title'),
        'importance': request.form.get('importance', 'normal')
    }
    save_task(task_data)
    return redirect(url_for('index'))

@app.route('/complete_task/<task_id>', methods=['POST'])
def complete_task(task_id):
    update_task_completion(task_id)
    return redirect(url_for('index'))

@app.route('/delete_task/<task_id>', methods=['POST'])
def delete_task(task_id):
    delete_task_by_id(task_id)
    return redirect(url_for('index'))

@app.route('/delete_all_tasks', methods=['POST'])
def delete_all_tasks():
    with open(TASKS_FILE, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
    return redirect(url_for('index'))

def run_flask():
    app.run(debug=True, use_reloader=False, threaded=True)

# Start the Flask app and the webview
def start_desktop_app():
    threading.Thread(target=run_flask).start()

    # Create and show the WebView window
    webview.create_window('Task Manager', 'http://127.0.0.1:5000')  # Point to your Flask app URL
    webview.start()
    

# if __name__ == '__main__':
#     init_csv()
#     app.run(debug=True)
if __name__ == '__main__':
    start_desktop_app()