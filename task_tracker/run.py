import json
import signal
from app import create_app
from flask_kafka import FlaskKafka
from models import db, User
from threading import Event
from settings import USER_CREATED_EVENT_VERSION
from utils import validate_schema


app = create_app({
    'SECRET_KEY': 'secret',
    'OAUTH2_REFRESH_TOKEN_GENERATOR': True,
    'SQLALCHEMY_TRACK_MODIFICATIONS': True,
    'SQLALCHEMY_DATABASE_URI': 'postgresql://admin:steve808.@localhost:5432/postgres'
})

# from task_tracker import db
# db.create_all(app=app)


INTERRUPT_EVENT = Event()
event_bus = FlaskKafka(
    INTERRUPT_EVENT,
    bootstrap_servers=",".join(["localhost:9092"]),
    group_id="task-tracker"
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


event_bus.run()
listen_kill_server()
app.run(host='127.0.0.1', port=8081)

