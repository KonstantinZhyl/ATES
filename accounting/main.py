import datetime
from flask import Blueprint
from flask_login import login_required, current_user
from flask import render_template
from models import db, AuditLog, User
from sqlalchemy import func


main = Blueprint('main', __name__)


def split_by_crlf(s):
    return [v for v in s.splitlines() if v]


@main.route('/')
@login_required
def index():
    return render_template('index.html')


@main.route('/balance')
@login_required
def balance():
    if current_user.is_manager():
        current_date = datetime.date.today()
        logs = db.session.query(User.email, func.sum(AuditLog.debit), func.sum(AuditLog.credit))\
            .filter(AuditLog.date == current_date).group_by(User.email).join(User).all()
        balances = [{'user': log[0], 'balance': log[1] - log[2]} for log in logs]

        return render_template('balance.html', balances=balances)
    else:
        current_date = datetime.date.today()
        logs = AuditLog.query.filter_by(date=current_date, user_id=current_user.id).all()
        balance = sum([log.debit for log in logs]) - sum([log.credit for log in logs])
        return render_template('balance.html', balance=balance, logs=logs)


@main.route('/analytics')
@login_required
def analytics():
    if current_user.is_admin():
        current_date = datetime.date.today()
        logs = db.session.query(User.email, func.sum(AuditLog.debit), func.sum(AuditLog.credit))\
            .filter(AuditLog.date == current_date).group_by(User.email).join(User).all()
        balances = [{'user': log[0], 'balance': log[1] - log[2]} for log in logs]
        debtors = len([popug for popug in balances if popug['balance'] < 0])
        managers_balance = -1 * sum([popug['balance'] for popug in balances])

        tasks_daily = db.session.query(AuditLog.date, func.max(AuditLog.debit)).group_by(AuditLog.date).join(User).all()
        tasks_monthly = db.session.query(func.to_char(AuditLog.date, 'YYYY-MM'), func.max(AuditLog.debit))\
            .group_by(func.to_char(AuditLog.date, 'YYYY-MM')).join(User).all()

        return render_template('analytics.html', debtors=debtors, managers_balance=managers_balance,
                               tasks_daily=tasks_daily, tasks_monthly=tasks_monthly)
