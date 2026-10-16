from flask import render_template, request, redirect, url_for, session, flash,  make_response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from extensions import db
from models import User, Habit, UserHabit, HabitLog
from os import abort
import uuid
import os


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def register_routes(app):
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
            return redirect(url_for('home'))
        theme = request.cookies.get('theme', 'standard')
        return render_template('main.html', user = user, theme = theme)


    @app.route('/profile/<string:username>', methods=['GET', 'POST'])
    def profile(username):
        user = User.query.filter_by(username=username).first()
        if not user:
            return abort(404)

        if session.get('user_id') != user.id:
            return abort(404)
        return render_template('profile.html', user=user)


    @app.route('/habits', methods = ['GET', 'POST'])
    def habits():
        habits = Habit.query.all()
        user = get_current_user()
        if not user:
            return redirect(url_for('home'))

        return render_template('habits.html', habits=habits)


    @app.route('/toggle/<int:habit_id>')
    def toggle_habit(habit_id):
        user = get_current_user()
        if not user:
            return redirect(url_for('home'))

        habit = Habit.query.get(habit_id)
        if not habit:
            return redirect(url_for('habits'))

        user_habit = UserHabit.query.filter_by(user_id = user.id, habit_id = habit_id).first()
        if not user_habit:
            user_habit_new = UserHabit(user_id = user.id, habit_id = habit_id)
            db.session.add(user_habit_new)
        else:
            db.session.delete(user_habit)

        db.session.commit()
        return redirect(url_for('habits'))


    @app.route('/tracking')
    def tracking():
        user = get_current_user()
        if not user:
            return redirect(url_for('home'))

        habits = UserHabit.query.filter_by(user_id=user.id).all()

        result = []
        for object_i in habits:
            name = Habit.query.get(object_i.habit_id).name
            log = HabitLog.query.filter_by(user_habit_id=object_i.id).first()
            count = log.count if log else 0
            habit_id = object_i.habit_id
            result.append([name, count, habit_id])

        return render_template('tracking.html', result=result)


    @app.route('/add/<int:habit_id>')
    def add_log(habit_id):
        user = get_current_user()
        if not user:
            return redirect(url_for('home'))

        user_habit = UserHabit.query.filter_by(user_id=user.id, habit_id=habit_id).first()
        if not user_habit:
            return redirect(url_for('tracking'))

        habit_log = HabitLog.query.filter_by(user_habit_id=user_habit.id).first()
        if not habit_log:
            new_habit_log = HabitLog(user_habit_id=user_habit.id, count=1)
            db.session.add(new_habit_log)
            db.session.commit()
        else:
            habit_log.count += 1
            db.session.commit()

        return redirect(url_for('tracking'))


    @app.route('/add_avatar', methods = ['GET', 'POST'])
    def add_avatar():
        user = get_current_user()
        if not user:
            return redirect(url_for('home'))

        if request.method == 'POST':
            file = request.files.get('avatar')

            if file and file.filename != '':
                if not allowed_file(file.filename):
                    return redirect(url_for('profile', username=user.username))

                filename = secure_filename(file.filename)

                unique_filename = f"{uuid.uuid4().hex}_{filename}"

                if user.avatar:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], user.avatar)
                    if os.path.exists(old_path):
                        os.remove(old_path)

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
            return redirect(url_for('home'))
        return render_template('info_vision.html')


    @app.route('/info_tonus')
    def information_two():
        user = get_current_user()
        if not user:
            return redirect(url_for('home'))
        return render_template('info_tonus.html')


    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('home'))


    @app.errorhandler(404)
    def page_not_found(error):
        return "Такой страницы не существует! \n Вернитесь на исходную страницу", 404
