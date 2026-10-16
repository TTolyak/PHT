from flask import Flask
from config import Config
from extensions import db, migrate
from models import User, Habit, UserHabit, HabitLog
from routes import register_routes


app = Flask(__name__)
@app.cli.command('seed-habits')
def seed_habits():
    if not Habit.query.first():
        habits = ['Пробежка', 'Вода', 'Чтение', 'Медитация']
        for name in habits:
            db.session.add(Habit(name=name))
        db.session.commit()
        print('Привычки добавлены')
    else:
        print('Привычки уже есть')
app.config.from_object(Config)

db.init_app(app)
migrate.init_app(app, db)

register_routes(app)


if __name__ == '__main__':
    app.run(debug=True, host = '0.0.0.0', port = 8000)