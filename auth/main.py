import time
from flask import Blueprint, request
from flask_login import login_required, current_user
from models import db, OAuth2Client, OAuth2Token, User
from werkzeug.security import gen_salt
from flask import render_template, redirect

main = Blueprint('main', __name__)

def split_by_crlf(s):
    return [v for v in s.splitlines() if v]

@main.route('/')
def index():
    return render_template('index.html')


@main.route('/profile')
@login_required
def profile():
    clients_list = OAuth2Client.query.all()
    return render_template('balance.html', name=current_user.name, clients_list=clients_list)


@main.route('/create_client', methods=('GET', 'POST'))
@login_required
def create_client():
    if request.method == 'GET':
        return render_template('create_client.html')

    client_id = gen_salt(24)
    client_id_issued_at = int(time.time())
    client = OAuth2Client(
        client_id=client_id,
        client_id_issued_at=client_id_issued_at,
    )

    form = request.form
    client_metadata = {
        "client_name": form["client_name"],
        "client_uri": form["client_uri"],
        "grant_types": split_by_crlf(form["grant_type"]),
        "redirect_uris": split_by_crlf(form["redirect_uri"]),
        "response_types": split_by_crlf(form["response_type"]),
        "scope": form["scope"],
        "token_endpoint_auth_method": form["token_endpoint_auth_method"]
    }
    client.set_client_metadata(client_metadata)

    if form['token_endpoint_auth_method'] == 'none':
        client.client_secret = ''
    else:
        client.client_secret = gen_salt(48)

    db.session.add(client)
    db.session.commit()
    return redirect('/')


@main.route('/oauth/authorize/<client_id>', methods=['GET', 'POST'])
@login_required
def authorize(client_id):
    token = OAuth2Token.query.filter_by(client_id=client_id, user_id=current_user.id).first()

    if not token:
        token = OAuth2Token(
            client_id=client_id,
            user_id=current_user.id,
            access_token=gen_salt(24),
            token_type='basic',
            issued_at=1,
            access_token_revoked_at=1,
            refresh_token_revoked_at=1,
            expires_in=1,
        )
        db.session.add(token)
        db.session.commit()

    client = OAuth2Client.query.filter_by(client_id=client_id).first()

    return redirect(f'http://{client.client_metadata["client_uri"]}/login/{token.access_token}')


@main.route('/oauth/check_token/<access_token>', methods=['GET'])
def issue_token(access_token):
    token = OAuth2Token.query.filter_by(access_token=access_token).first()
    if token:
        user = User.query.filter_by(id=token.user_id).first()
        return {
            'status_code': 200,
            'data': {
                'user_id': user.public_id,
                'role': user.role.name,
            }
        }
    return {
        'status_code': 403
    }
