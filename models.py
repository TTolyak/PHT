from extensions import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80), unique = True, nullable = False)
    email = db.Column(db.String(120), unique = True, nullable = False)
    password_hash = db.Column(db.String(256), nullable = False)
    avatar = db.Column(db.String(200), nullable=True)


class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique = True, nullable = False)


class UserHabit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'), nullable = False)

    user = db.relationship('User', backref='user_habits')
    habit = db.relationship('Habit', backref='user_habits')


class HabitLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, nullable=False, default = 0)
    user_habit_id = db.Column(db.Integer, db.ForeignKey('user_habit.id'))

    userhabit = db.relationship('UserHabit', backref='habit_logs')
