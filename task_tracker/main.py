from random import randint
from flask import Blueprint, request, flash
from flask_login import login_required, current_user
from flask import render_template, redirect, url_for
from models import db, User, Task, UserRole, TaskStatus


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


@main.route('/create_task', methods=['POST'])
@login_required
def create_task_post():
    description = request.form.get('description')

    users = User.query.filter_by(role=UserRole.EMPLOYEE.name).all()

    if not len(users):
        flash('No available users to attach this task to')
        return redirect(url_for('main.create_task'))

    new_task = Task(description=description, user_id=users[randint(0, len(users) - 1)].id)

    # add the new user to the database
    db.session.add(new_task)
    db.session.commit()

    return redirect(url_for('main.profile'))


@main.route('/close_task/<task_id>')
@login_required
def close_task(task_id):
    task = Task.query.filter_by(id=task_id).first()
    task.status = TaskStatus.DONE.name
    db.session.commit()
    return redirect(url_for('main.profile'))


@main.route('/reassign_tasks')
@login_required
def reassign_tasks():
    users = User.query.filter_by(role=UserRole.EMPLOYEE.name).all()
    tasks = Task.query.filter_by(status=TaskStatus.IN_PROGRESS.name).all()
    for task in tasks:
        task.user_id = users[randint(0, len(users) - 1)].id
    db.session.commit()
    flash('Tasks reassigned!')
    return redirect(url_for('main.profile'))
