import enum
import uuid
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import Enum


db = SQLAlchemy()


class UserRole(enum.Enum):
    __table_args__ = {'schema': 'task_tracker'}
    EMPLOYEE = 'employee'
    MANAGER = 'manager'
    ADMIN = 'admin'


class User(UserMixin, db.Model):
    __table_args__ = {'schema': 'accounting'}
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), default=uuid.uuid4)
    email = db.Column(db.String(100), unique=True)
    role = db.Column(Enum(UserRole), default=UserRole.EMPLOYEE.name)

    def is_admin(self):
        return self.role == UserRole.ADMIN

    def is_manager(self):
        return self.role in (UserRole.ADMIN, UserRole.MANAGER)


class Task(db.Model):
    __table_args__ = {'schema': 'accounting'}
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)
    description = db.Column(db.String(100), unique=True, nullable=False)
    close_price = db.Column(db.Integer)
    assign_price = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id, ondelete='CASCADE'))


class AuditLog(db.Model):
    __table_args__ = {'schema': 'accounting'}
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey(Task.id, ondelete='CASCADE'))
    transaction_id = db.Column(db.String(100))
    description = db.Column(db.String(100), nullable=False)
    debit = db.Column(db.Integer, default=0)
    credit = db.Column(db.Integer, default=0)
    date = db.Column(db.Date)
    created_at = db.Column(db.DateTime)
