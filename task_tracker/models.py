import enum
import uuid
from flask_login import UserMixin
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import Enum


db = SQLAlchemy()
migrate = Migrate()


class UserRole(enum.Enum):
    __table_args__ = {'schema': 'task_tracker'}
    EMPLOYEE = 'employee'
    MANAGER = 'manager'
    ADMIN = 'admin'


class TaskStatus(enum.Enum):
    __table_args__ = {'schema': 'task_tracker'}
    IN_PROGRESS = 'in_progress'
    DONE = 'done'


class User(UserMixin, db.Model):
    __table_args__ = {'schema': 'task_tracker'}
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), default=uuid.uuid4)
    email = db.Column(db.String(100), unique=True)
    role = db.Column(Enum(UserRole), default=UserRole.EMPLOYEE.name)

    def is_admin(self):
        return self.role == UserRole.ADMIN.name

    def is_manager(self):
        return self.role in (UserRole.ADMIN.name, UserRole.MANAGER.name)


class Task(db.Model):
    __table_args__ = {'schema': 'task_tracker'}
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)
    description = db.Column(db.String(100), unique=True, nullable=False)
    jira_id = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(Enum(TaskStatus), default=TaskStatus.IN_PROGRESS.name)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id, ondelete='CASCADE'))
