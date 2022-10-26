import atexit
import datetime
import json
import signal
from app import create_app
from flask_kafka import FlaskKafka
from models import db, AuditLog, Task, User, UserRole
from random import randint
from threading import Event
from werkzeug.security import generate_password_hash
from apscheduler.schedulers.background import BackgroundScheduler
from settings import (
    TASK_CLOSED_EVENT_VERSION, TASK_CREATED_EVENT_VERSION, TASKS_REASSIGNED_EVENT_VERSION, USER_CREATED_EVENT_VERSION)
from utils import validate_schema

app = create_app({
    'SECRET_KEY': 'secret',
    'OAUTH2_REFRESH_TOKEN_GENERATOR': True,
    'SQLALCHEMY_TRACK_MODIFICATIONS': True,
    'SQLALCHEMY_DATABASE_URI': 'postgresql://admin:steve808.@localhost:5432/postgres'
})

db.create_all(app=app)


INTERRUPT_EVENT = Event()
event_bus = FlaskKafka(
    INTERRUPT_EVENT,
    bootstrap_servers=','.join(['localhost:9092']),
    group_id='accounting'
)


def listen_kill_server():
    signal.signal(signal.SIGTERM, event_bus.interrupted_process)
    signal.signal(signal.SIGINT, event_bus.interrupted_process)
    signal.signal(signal.SIGQUIT, event_bus.interrupted_process)
    signal.signal(signal.SIGHUP, event_bus.interrupted_process)


@event_bus.handle('accounts-stream')
def accounts_stream_topic_handler(msg):
    event = json.loads(msg.value.decode())
    print(event)

    if event['event_name'] == 'user.created':
        if event['event_version'] == USER_CREATED_EVENT_VERSION \
                and validate_schema('user.created', USER_CREATED_EVENT_VERSION, event):
            user_data = event['user']
            with app.app_context():
                user = User(email=user_data['email'], public_id=user_data['public_id'], role=user_data['role'])
                db.session.add(user)
                db.session.commit()
            print('New user added to our db')


@event_bus.handle('tasks-stream')
def tasks_stream_topic_handler(msg):
    event = json.loads(msg.value.decode())
    print(event)

    if event['event_name'] == 'task.created':
        if event['event_version'] == TASK_CREATED_EVENT_VERSION \
                and validate_schema('task.created', TASK_CREATED_EVENT_VERSION, event):
            task_data = event['task']
            with app.app_context():
                user = User.query.filter_by(public_id=task_data['user_id']).first()
                assign_price = randint(10, 20)
                close_price = randint(20, 40)
                task = Task(
                    description=task_data['description'],
                    jira_id=task_data['jira_id'],
                    public_id=task_data['public_id'],
                    user_id=user.id,
                    assign_price=assign_price,
                    close_price=close_price,
                )
                db.session.add(task)
                db.session.commit()

                audit_log = AuditLog(
                    user_id=user.id,
                    task_id=task.id,
                    transaction_id=generate_password_hash(f'{datetime.date.today()}/{user.id}', method='sha256'),
                    description='Task assigned on creation',
                    debit=0,
                    credit=assign_price,
                    date=datetime.date.today(),
                    created_at=datetime.datetime.now(),
                )
                db.session.add(audit_log)
                db.session.commit()
            print('New task created')

    if event['event_name'] == 'task.closed':
        if event['event_version'] == TASK_CLOSED_EVENT_VERSION \
                and validate_schema('task.closed', TASK_CLOSED_EVENT_VERSION, event):
            task_data = event['task']
            with app.app_context():
                task = Task.query.filter_by(public_id=task_data['public_id']).first()

                audit_log = AuditLog(
                    user_id=task.user_id,
                    task_id=task.id,
                    transaction_id=generate_password_hash(f'{datetime.date.today()}/{user.id}', method='sha256'),
                    description='Task closed',
                    debit=task.close_price,
                    credit=0,
                    date=datetime.date.today(),
                    created_at=datetime.datetime.now(),
                )
                db.session.add(audit_log)
                db.session.commit()
            print('Task closed')

    if event['event_name'] == 'tasks.reassigned':
        if event['event_version'] == TASKS_REASSIGNED_EVENT_VERSION \
                and validate_schema('tasks.reassigned', TASKS_REASSIGNED_EVENT_VERSION, event):
            mapping = event['data']['user_task_mapping']
            with app.app_context():
                for item in mapping:
                    user = User.query.filter_by(public_id=item['user_id']).first()
                    task = Task.query.filter_by(public_id=item['task_id']).first()
                    audit_log = AuditLog(
                        user_id=user.id,
                        task_id=task.id,
                        transaction_id=generate_password_hash(f'{datetime.date.today()}/{user.id}', method='sha256'),
                        description='Task assigned',
                        debit=0,
                        credit=task.assign_price,
                        date=datetime.date.today(),
                        created_at=datetime.datetime.now(),
                    )
                    db.session.add(audit_log)
                    db.session.commit()
            print('Tasks reassigned')




def send_payslip(user: User, payment_amount: int):
    pass


def close_daily_transactions():
    date = datetime.date.today() - datetime.timedelta(days=1)
    with app.app_context():
        users = User.query.filter_by(role=UserRole.EMPLOYEE).all()
        for user in users:
            logs = AuditLog.query.filter_by(user_id=user.id, date=date).all()
            balance = sum([log.debit for log in logs]) - sum([log.credit for log in logs])
            if balance > 0:
                payment_transaction = AuditLog(
                    user_id=user.id,
                    task_id=None,
                    transaction_id=generate_password_hash(f'{date}/{user.id}', method='sha256'),
                    description='Payment',
                    debit=0,
                    credit=abs(balance),
                    date=date,
                    created_at=datetime.datetime.now(),
                )
                db.session.add(payment_transaction)
            else:
                payment_transaction = AuditLog(
                    user_id=user.id,
                    task_id=None,
                    transaction_id=generate_password_hash(f'{date}/{user.id}', method='sha256'),
                    description='Debt fixation',
                    debit=abs(balance),
                    credit=0,
                    date=date,
                    created_at=datetime.datetime.now(),
                )
                db.session.add(payment_transaction)

                next_day_date = date + datetime.timedelta(days=1)
                debt_transaction = AuditLog(
                    user_id=user.id,
                    task_id=None,
                    transaction_id=generate_password_hash(f'{next_day_date}/{user.id}', method='sha256'),
                    description='Debt',
                    debit=0,
                    credit=abs(balance),
                    date=next_day_date,
                    created_at=datetime.datetime.now(),
                )
                db.session.add(debt_transaction)
            db.session.commit()
            send_payslip(user, balance)
    print('Daily transactions closed!')


scheduler = BackgroundScheduler()
scheduler.add_job(close_daily_transactions, 'cron', day_of_week='mon-sun', hour=0, minute=0)
scheduler.start()

event_bus.run()
listen_kill_server()
app.run(host='127.0.0.1', port=8082)

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())
