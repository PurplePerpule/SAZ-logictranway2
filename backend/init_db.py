from app import Vehicle, User, Location, app, db
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

sample_users = [
    {
        "username": "ivanov",
        "password": "password123",
        "role": "user",
        "full_name": "Иванов Иван Иванович",
        "department": "Отдел логистики",
        "phone_number": "+375 29 123-45-67"
    },
    {
        "username": "petrov",
        "password": "password456",
        "role": "user",
        "full_name": "Петров Петр Петрович",
        "department": "Производственный отдел",
        "phone_number": "+375 29 234-56-78"
    },
    {
        "username": "sidorova",
        "password": "password789",
        "role": "user",
        "full_name": "Сидорова Мария Сергеевна",
        "department": "Отдел снабжения",
        "phone_number": "+375 29 345-67-89"
    },
    {
        "username": "admin",
        "password": "sazadmin2025",
        "role": "admin",
        "full_name": "Администратор Системы",
        "department": "Администрация",
        "phone_number": "+375 17 123-45-67"
    }
]

sample_locations = [
    {
        "company_name": "Сморгонский агрегатный завод",
        "address": "г. Сморгонь, ул. Советская, 150",
        "is_departure": True,
        "is_destination": False,
        "contact_person": "Отдел логистики",
        "phone_number": "+375 1592 12345"
    },
    {
        "company_name": "Минский завод строительных материалов",
        "address": "г. Минск, ул. Строителей, 25",
        "is_departure": False,
        "is_destination": True
    },
    {
        "company_name": "Витебский машиностроительный завод",
        "address": "г. Витебск, пр-т Московский, 150",
        "is_departure": False,
        "is_destination": True
    },
    {
        "company_name": "Гродненский металлопрокат",
        "address": "г. Гродно, ул. Промышленная, 15",
        "is_departure": True,
        "is_destination": True
    },
    {
        "company_name": "Брестский порт",
        "address": "г. Брест, ул. Портовая, 1",
        "is_departure": True,
        "is_destination": True
    },
    {
        "company_name": "Гомельский химический завод",
        "address": "г. Гомель, ул. Химиков, 30",
        "is_departure": False,
        "is_destination": True
    },
    {
        "company_name": "Могилевский автозавод",
        "address": "г. Могилев, ул. Автозаводская, 10",
        "is_departure": True,
        "is_destination": True
    }
]



with app.app_context():
    # Создаем все таблицы
    db.create_all()

    # Добавляем пользователей
    for user_data in sample_users:
        if not User.query.filter_by(username=user_data["username"]).first():
            user = User(
                username=user_data["username"],
                password=generate_password_hash(user_data["password"]),
                role=user_data["role"],
                full_name=user_data["full_name"],
                department=user_data["department"],
                phone_number=user_data["phone_number"]
            )
            db.session.add(user)
            print(f"Added user: {user_data['username']}")

    # Добавляем транспортные средства
    if Vehicle.query.count() == 0:
        for veh in sample_vehicles:
            new_vehicle = Vehicle(**veh)
            db.session.add(new_vehicle)
        print("Sample vehicles added to the database.")

    # Добавляем адреса
    if Location.query.count() == 0:
        for loc_data in sample_locations:
            location = Location(**loc_data)
            db.session.add(location)
        print("Sample locations added to the database.")
    # Сохраняем все изменения
    db.session.commit()
    print("Database initialization complete!")
