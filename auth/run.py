from app import create_app


app = create_app({
    'SECRET_KEY': 'secret',
    'OAUTH2_REFRESH_TOKEN_GENERATOR': True,
    'SQLALCHEMY_TRACK_MODIFICATIONS': True,
    'SQLALCHEMY_DATABASE_URI': 'postgresql://admin:steve808.@localhost:5432/postgres'
})

# from auth import db
# db.create_all(app=app)

app.run(host='127.0.0.1', port=5000)
