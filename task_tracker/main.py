import datetime
import uuid
import re
from random import randint

from flask import Blueprint, request, flash
from flask_login import login_required, current_user
from flask import render_template, redirect, url_for
from kafka_producer import kafka_send_message
from models import db, User, Task, UserRole, TaskStatus
from utils import validate_schema
from settings import (TASK_CLOSED_EVENT_VERSION, TASK_CREATED_EVENT_VERSION, TASKS_REASSIGNED_EVENT_VERSION)


main = Blueprint('main', __name__)


def split_by_crlf(s):
    return [v for v in s.splitlines() if v]


@main.route('/')
@login_required
def index():
    return render_template('index.html')


@main.route('/profile')
@login_required
def profile():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', tasks=tasks)


@main.route('/create_task')
@login_required
def create_task():
    return render_template('create_task.html')


def _extract_jira_id(description):
    match = re.search(r'\[(.+)\]', description)
    if match:
        return match.groups()[0]
    return None


def _extract_description(description):
    match = re.search(r'\[(.+)\]\s*(.+)$', description)
    if match:
        return match.groups()[1]
    return description


@main.route('/create_task', methods=['POST'])
@login_required
def create_task_post():
    description = request.form.get('description')

    users = User.query.filter_by(role=UserRole.EMPLOYEE.name).all()

    if not len(users):
        flash('No available users to attach this task to')
        return redirect(url_for('main.create_task'))

    random_user = users[randint(0, len(users) - 1)]

    jira_id = _extract_jira_id(description)
    description = _extract_description(description)
    new_task = Task(jira_id=jira_id, description=description, user_id=random_user.id)

    # add the new user to the database
    db.session.add(new_task)
    db.session.commit()

    event = {
        'event_version': TASK_CREATED_EVENT_VERSION,
        'event_id': str(uuid.uuid4()),
        'event_name': 'task.created',
        'event_created_at': datetime.datetime.now().isoformat(),
        'task': {
            'description': new_task.description,
            'jira_id': jira_id,
            'user_id': str(random_user.public_id),
            'public_id': str(new_task.public_id),
        }
    }

    if validate_schema('task.created', TASK_CREATED_EVENT_VERSION, event):
        print('Task sent to kafka')
        kafka_send_message(message=event, topic='tasks-stream')

    return redirect(url_for('main.profile'))


@main.route('/close_task/<task_id>')
@login_required
def close_task(task_id):
    task = Task.query.filter_by(id=task_id).first()
    task.status = TaskStatus.DONE.name
    db.session.commit()

    event = {
        'event_version': TASK_CLOSED_EVENT_VERSION,
        'event_id': str(uuid.uuid4()),
        'event_name': 'task.closed',
        'event_created_at': datetime.datetime.now().isoformat(),
        'task': {
            'public_id': str(task.public_id),
        }
    }
    if validate_schema('task.closed', TASK_CLOSED_EVENT_VERSION, event):
        kafka_send_message(message=event, topic='tasks-stream')

    return redirect(url_for('main.profile'))


@main.route('/reassign_tasks')
@login_required
def reassign_tasks():
    users = User.query.filter_by(role=UserRole.EMPLOYEE.name).all()
    tasks = Task.query.filter_by(status=TaskStatus.IN_PROGRESS.name).all()
    user_task_mapping = []
    for task in tasks:
        user = users[randint(0, len(users) - 1)]
        task.user_id = user.id
        user_task_mapping.append({
            'user_id': str(user.public_id),
            'task_id': str(task.public_id),
        })
        db.session.commit()

    event = {
        'event_version': TASKS_REASSIGNED_EVENT_VERSION,
        'event_id': str(uuid.uuid4()),
        'event_name': 'tasks.reassigned',
        'event_created_at': datetime.datetime.now().isoformat(),
        'data': {
            'user_task_mapping': user_task_mapping,
        }
    }

    if validate_schema('tasks.reassigned', TASKS_REASSIGNED_EVENT_VERSION, event):
        kafka_send_message(message=event, topic='tasks-stream')
    flash('Tasks reassigned!')
    return redirect(url_for('main.profile'))
