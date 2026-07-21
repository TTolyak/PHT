from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import secrets
import os


app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

app.secret_key = secrets.token_hex(32)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80), unique = True, nullable = False)
    email = db.Column(db.String(120), unique = True, nullable = False)
    password_hash = db.Column(db.String(256), nullable = False)
    avatar = db.Column(db.String(200), nullable=True)

with app.app_context():
    db.create_all()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/main')
def main():
    username = session.get('username')
    user = User.query.filter_by(username=username).first()
    return render_template('main.html', user = user)

@app.route('/add_avatar', methods = ['GET', 'POST'])
def add_avatar():
    username = session.get('username')
    user = User.query.filter_by(username=username).first()
    if request.method == 'POST':
        file = request.files.get('avatar')

        if file and file.filename != '':
            if not allowed_file(file.filename):
                return redirect(url_for('profile', username=user.username))

            filename = secure_filename(file.filename)

            import uuid
            unique_filename = f"{uuid.uuid4().hex}_{filename}"

            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))

            user.avatar = unique_filename
            db.session.commit()

            return redirect(url_for('profile', username=user.username))
        else:
            return redirect(url_for('profile', username=user.username))

    return render_template('input_avatar.html', user=user)

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

        flash("Регистрация успешна!", "success")
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


@app.route('/profile/<string:username>', methods=['GET', 'POST'])
def profile(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return "Пользователь не найден", 404

    if session.get('user_id') != user.id:
        return "Ошибка доступа", 404
    return render_template('profile.html', user=user)


@app.route('/info_vision')
def information_one():
    return render_template('info_vision.html')


@app.route('/info_tonus')
def information_two():
    return render_template('info_tonus.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))


@app.errorhandler(404)
def page_not_found(error):
    return "Такой страницы не существует! \n Вернитесь на исходную страницу", 404


if __name__ == '__main__':
    app.run(debug=True, host = '0.0.0.0', port = 8000)