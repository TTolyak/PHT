from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os


app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

app.secret_key = 'd9f8c7b6a5e4d3c2b1a0f9e8d7c6b5a4d3c2b1a0f9e8d7c6b5a4d3c2b1a0f9e8d7c6'

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


def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.context_processor
def inject_theme():
    theme = request.cookies.get('theme', 'standard')
    return dict(theme=theme)


@app.route('/set-theme/<theme_name>')
def set_theme(theme_name):
    response = make_response(redirect(url_for('main')))
    response.set_cookie('theme', theme_name, max_age= 30 * 24 * 3600, path='/')
    return response


@app.route('/')
def home():
    return render_template('home.html')


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


@app.route('/main')
def main():
    user = get_current_user()
    if not user:
        redirect(url_for('home'))
    theme = request.cookies.get('theme', 'standard')
    return render_template('main.html', user = user, theme = theme)



@app.route('/profile/<string:username>', methods=['GET', 'POST'])
def profile(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return "Пользователь не найден", 404

    if session.get('user_id') != user.id:
        return "Ошибка доступа", 404
    return render_template('profile.html', user=user)


@app.route('/add_avatar', methods = ['GET', 'POST'])
def add_avatar():
    user = get_current_user()
    if not user:
        redirect(url_for('home'))

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

# Сделать флеш-сообщения и перенаправления на эту же страницу при неверных данных
@app.route('/change_password', methods = ['GET', 'POST'])
def change_password():
    user = get_current_user()
    if not user:
        return redirect(url_for('home'))

    if request.method == 'POST':
        old_password = request.form.get('password_one')
        new_password = request.form.get('password_two')
        confirm_password = request.form.get('password_three')

        if not check_password_hash(user.password_hash, old_password):
            return "Старый пароль неверен", 400

        if new_password != confirm_password:
            return "Не совпадают", 400

        user.password_hash = generate_password_hash(new_password)
        db.session.commit()

        return redirect(url_for('profile', username=user.username))

    return render_template('change_password.html', user = user)


@app.route('/info_vision')
def information_one():
    user = get_current_user()
    if not user:
        redirect(url_for('home'))
    return render_template('info_vision.html')


@app.route('/info_tonus')
def information_two():
    user = get_current_user()
    if not user:
        redirect(url_for('home'))
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