# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import csv
import os
import uuid

app = Flask(__name__)

# CSV file setup
TASKS_FILE = 'tasks.csv'
FIELDNAMES = ['id', 'title', 'start_time', 'completion_time', 'time_taken', 'importance', 'status', 'created_at']

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

if __name__ == '__main__':
    init_csv()
    app.run(debug=True)