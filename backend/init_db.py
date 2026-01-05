from app import Vehicle, User, app, db
from werkzeug.security import generate_password_hash


sample_vehicles = [
    {
        "garage_number": 1,
        "brand": "ГАЗ 3302",
        "driver": "Гуринович А.В.",
        "gos_number": "АВ 6101-4",
        "capacity": 1500.0,
        "length": 3.0,
        "width": 2.2,
        "height": 1.750,
        "status": "free",
        "tent_type": "closed"
    },
    {
        "garage_number": 7,
        "brand": "ГАЗ 3302",
        "driver": "Клевцов Ю.В.",
        "gos_number": "АВ 6100-4",
        "capacity": 1500.0,
        "length": 3.0,
        "width": 2.2,
        "height": 1.750,
        "status": "free",
        "tent_type": "closed"
    },
    {
        "garage_number": 8,
        "brand": "ГАЗ А22 R23-50",
        "driver": "Докурно Р.М.",
        "gos_number": "АМ 7485-4",
        "capacity": 1500.0,
        "length": 2.0,
        "width": 2.2,
        "height": 1.750,
        "status": "free",
        "tent_type": "closed"
    },
    {
        "garage_number": 16,
        "brand": "МАЗ 4371",
        "driver": "Жданюк В.В.",
        "gos_number": "АВ 7555-4",
        "capacity": 5000.0,
        "length": 6.0,
        "width": 2.4,
        "height": 2.3,
        "status": "free",
        "tent_type": "closed"
    },
    {
        "garage_number": 17,
        "brand": "МАЗ 5440А5",
        "driver": "Гулецкий А.Э.",
        "gos_number": "АH 0425-4",
        "capacity": 20000.0,
        "length": 13.7,
        "width": 2.4,
        "height": 2.4,
        "status": "free",
        "tent_type": "closed"
    },
    {
        "garage_number": 12,
        "brand": "МАЗ 4370",
        "driver": "Кособутский В.А.",
        "gos_number": "7349 АВ-4",
        "capacity": 5000.0,
        "length": 6.0,
        "width": 2.4,
        "height": 2.2,
        "status": "free",
        "tent_type": "closed"
    },
    {
        "garage_number": 290,
        "brand": "МАЗ 5340 В5",
        "driver": "Вишняк И.И.",
        "gos_number": "АК 4925-4",
        "capacity": 20000.0,
        "length": 6.0,
        "width": 2.4,
        "height": 2.600,
        "status": "free",
        "tent_type": "open"
    },
    {
        "garage_number": 32,
        "brand": "МАЗ 5440С9",
        "driver": "Граматовский В.И.",
        "gos_number": "АМ 9310-4",
        "capacity": 20000.0,
        "length": 13.7,
        "width": 2.4,
        "height": 2.4,
        "status": "free",
        "tent_type": "closed"
    },
    {
        "garage_number": 34,
        "brand": "МАЗ 544028",
        "driver": "Клакевич И.Н.",
        "gos_number": "АМ 9397-4",
        "capacity": 20000.0,
        "length": 13.7,
        "width": 2.4,
        "height": 2.4,
        "status": "free",
        "tent_type": "closed"
    },
    {
        "garage_number": 35,
        "brand": "ГАЗ А31 R32",
        "driver": "Воронович С.Ч.",
        "gos_number": "АН 5280-4",
        "capacity": 1100.0,
        "length": 3.6,
        "width": 1.8,
        "height": 1.9,
        "status": "free",
        "tent_type": "closed"
    },
    {
        "garage_number": 37,
        "brand": "МАЗ 4371",
        "driver": "Мартусевич Д.Е.",
        "gos_number": "AI 9499-4",
        "capacity": 5000.0,
        "length": 6.0,
        "width": 2.4,
        "height": 2.3,
        "status": "free",
        "tent_type": "closed"
    },
    {
        "garage_number": 39,
        "brand": "МАЗ 5440А8",
        "driver": "Лисовский А.Э.",
        "gos_number": "AA 8218-4",
        "capacity": 20000.0,
        "length": 13.7,
        "width": 2.4,
        "height": 2.750,
        "status": "free",
        "tent_type": "open"
    },
    {
        "garage_number": 40,
        "brand": "МАЗ 5440С9",
        "driver": "Кохановский В.З.",
        "gos_number": "АН 7177-4",
        "capacity": 20000.0,
        "length": 13.7,
        "width": 2.4,
        "height": 2.6,
        "status": "free",
        "tent_type": "open"
    },
    {
        "garage_number": 60,
        "brand": "МАЗ 5340B5",
        "driver": "Нет водителя",
        "gos_number": "АI 9623-4",
        "capacity": 9000.0,
        "length": 6.0,
        "width": 2.4,
        "height": 2.4,
        "status": "free",
        "tent_type": "closed"
    },
    {
        "garage_number": 61,
        "brand": "ГАЗ 2218",
        "driver": "Станкевич И.В.",
        "gos_number": "АB 7878-4",
        "capacity": 3000.0,
        "length": 4.0,
        "width": 2.4,
        "height": 2.2,
        "status": "free",
        "tent_type": "closed"
    },
    {
        "garage_number": 62,
        "brand": "МАЗ 543205",
        "driver": "Медовский И.М.",
        "gos_number": "АI 2592-4",
        "capacity": 20000.0,
        "length": 13.7,
        "width": 2.4,
        "height": 0.5,
        "status": "free",
        "tent_type": "open"
    },
]

with app.app_context():
    # Создаем все таблицы
    db.create_all()

    # Добавляем пользователей, если их нет
    if User.query.count() == 0:
        user = User(username="user", password=generate_password_hash("sazwork205"), role="user")
        admin = User(username="admin", password=generate_password_hash("sazadmin2025"), role="admin")
        db.session.add(user)
        db.session.add(admin)
        print("Default users added to the database.")

    # Добавляем транспортные средства, если их нет
    if Vehicle.query.count() == 0:
        for veh in sample_vehicles:
            new_vehicle = Vehicle(**veh)
            db.session.add(new_vehicle)
        print("Sample vehicles added to the database.")

    # Сохраняем все изменения
    db.session.commit()
    print("Database initialization complete!")
