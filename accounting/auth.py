# auth.py
import requests
from flask import Blueprint, render_template, redirect
from flask_login import login_user, logout_user, login_required
from models import User

auth = Blueprint('auth', __name__)


@auth.route('/login/<access_token>')
def login(access_token):
    response = requests.get(f'http://127.0.0.1:5000/oauth/check_token/{access_token}')
    response_json = response.json()
    if response_json['status_code'] == 200:
        user = User.query.filter_by(public_id=response_json['data']['user_id']).first()
        print(f'User {user.email} signed in!')
        login_user(user, remember=True)
    else:
        render_template('403.html')

    return redirect('/')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('http://127.0.0.1:5000')