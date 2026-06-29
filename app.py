from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask
from flask import render_template
from flask import request
from flask import redirect, url_for
from flask import session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import secrets

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.secret_key = secrets.token_hex(32)

db = SQLAlchemy(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80), unique = True, nullable = False)
    email = db.Column(db.String(120), unique = True, nullable = False)
    password_hash = db.Column(db.String(256), nullable = False)

with app.app_context():
    db.create_all()


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/main')
def main():
    return render_template('main.html')


@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Пользователь с таким именем уже существует"

        new_user = User(username=username, email = email, password_hash = generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('home'))

    return render_template('register.html')


@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('main'))
        else:
            return "Неверное имя пользователя или пароль"

    return render_template('login.html')


@app.route('/profile/<string:username>', methods = ['GET'])
def profile(username):
    user = User.query.filter_by(username=username).first()
    if not user: return "Пользователь не найден", 404
    if session.get('user_id') == user.id:
        return render_template('profile.html', user=user)
    else: return "Ошибка доступа", 404


@app.errorhandler(404)
def page_not_found(error):
    return "Такой страницы не существует! \n Вернитесь на исходную страницу", 404


if __name__ == '__main__':
    app.run(debug=True, host = '0.0.0.0', port = 8000)