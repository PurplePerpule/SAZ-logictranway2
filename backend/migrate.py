from app import app, db
from sqlalchemy import text

with app.app_context():
    # Проверяем существование колонок
    conn = db.engine.connect()

    # Проверяем и добавляем колонку user_id в таблицу order
    try:
        conn.execute(text("SELECT user_id FROM `order` LIMIT 1"))
        print("Колонка user_id уже существует в таблице order")
    except:
        print("Добавляем колонку user_id в таблицу order...")
        conn.execute(text("ALTER TABLE `order` ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1 REFERENCES user(id)"))

    # Проверяем и добавляем колонку user_id в таблицу draft_cargo
    try:
        conn.execute(text("SELECT user_id FROM draft_cargo LIMIT 1"))
        print("Колонка user_id уже существует в таблице draft_cargo")
    except:
        print("Добавляем колонку user_id в таблицу draft_cargo...")
        conn.execute(text("ALTER TABLE draft_cargo ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1 REFERENCES user(id)"))

    # Проверяем и добавляем новые колонки в таблицу user
    try:
        conn.execute(text("SELECT full_name FROM user LIMIT 1"))
        print("Колонки уже существуют в таблице user")
    except:
        print("Добавляем колонки в таблицу user...")
        conn.execute(text("ALTER TABLE user ADD COLUMN full_name VARCHAR(100)"))
        conn.execute(text("ALTER TABLE user ADD COLUMN department VARCHAR(100)"))
        conn.execute(text("ALTER TABLE user ADD COLUMN phone_number VARCHAR(20)"))

    try:
        conn.execute(text("SELECT preferred_departure_time FROM `order` LIMIT 1"))
        print("Колонка preferred_departure_time уже существует в таблице order")
    except:
        print("Добавляем колонку preferred_departure_time в таблицу order...")
        conn.execute(text("ALTER TABLE `order` ADD COLUMN preferred_departure_time DATETIME"))

    conn.close()
    print("Миграция завершена успешно!")
