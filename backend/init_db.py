from app import Vehicle, app, db

# Sample vehicles data
sample_vehicles = [
    {
        "brand": "ГАЗ 3302",
        "driver": "Гуринович А.В.",
        "capacity": 1500.0,  # in kg
        "status": "free",
    },
    {
        "brand": "VOLKSWAGEN",
        "driver": "Герко К.Р.",
        "capacity": 2000.0,
        "status": "free",
    },
    {
        "brand": "ГАЗ 2705 ",
        "driver": "Артеменко В.И.",
        "capacity": 3000.0,
        "status": "busy",
    },
    {
        "brand": "ГАЗ 3302",
        "driver": "Клевцов Ю.В.",
        "capacity": 5000.0,
        "status": "free",
    },
    {
        "brand": "ГАЗ А22R23",
        "driver": "Докурно Р.М.",
        "capacity": 5000.0,
        "status": "free",
    },
    {
        "brand": "GEELY",
        "driver": "Поцелуйко Д.А.",
        "capacity": 5000.0,
        "status": "free",
    },
    {
        "brand": "GEELY",
        "driver": "Зинкевич М.М.",
        "capacity": 5000.0,
        "status": "free",
    },
    {
        "brand": "ГАЗ 2705 ",
        "driver": "Перепечкин Е.А.",
        "capacity": 5000.0,
        "status": "free",
    },
    {
        "brand": "МАЗ 437143 ",
        "driver": "Жданюк В.В.",
        "capacity": 5000.0,
        "status": "free",
    },
    {
        "brand": "МАЗ 5440 А5 ",
        "driver": "Гулецкий А.Э.",
        "capacity": 5000.0,
        "status": "free",
    },
    {
        "brand": "ГАЗ А65R52",
        "driver": "Ерман В.Г.",
        "capacity": 5000.0,
        "status": "free",
    },
    {
        "brand": "МАЗ 437043",
        "driver": "Кособудский В.А.",
        "capacity": 5000.0,
        "status": "free",
    },
    {
        "brand": "ГАЗ А31 R32-580",
        "driver": "Кайрис В.И.",
        "capacity": 5000.0,
        "status": "free",
    },
    {
        "brand": "МАЗ 5340 В5",
        "driver": "Вишняк И.И.",
        "capacity": 5000.0,
        "status": "free",
    },
    {
        "brand": "МАЗ 5440 С9",
        "driver": "Граматовский В.И.",
        "capacity": 5000.0,
        "status": "free",
    },
    {
        "brand": "ГАЗ А31 R33",
        "driver": "Шапель А.М.",
        "capacity": 5000.0,
        "status": "free",
    },
    {
        "brand": "МАЗ 544028",
        "driver": "Клакевич И.Н.",
        "capacity": 5000.0,
        "status": "free",
    },
    {
        "brand": "ГАЗ А32",
        "driver": "Воронович С.Ч.",
        "capacity": 5000.0,
        "status": "free",
    },
    {
        "brand": "ГАЗ 2705",
        "driver": "Бумбуль В.З.",
        "capacity": 5000.0,
        "status": "free",
    },
    {
        "brand": "МАЗ 4371 З2",
        "driver": "Мартусевич Д.Е.",
        "capacity": 5000.0,
        "status": "free",
    },
    {
        "brand": "МАЗ 5440 А8",
        "driver": "Лисовский А.Э.",
        "capacity": 5000.0,
        "status": "free",
    },
    {
        "brand": "МАЗ 5440 С9",
        "driver": "Кохоновский В.З.",
        "capacity": 5000.0,
        "status": "free",
    },
    {
        "brand": "МАЗ 5551",
        "driver": "Медовский И.С.",
        "capacity": 5000.0,
        "status": "free",
    },
]

with app.app_context():
    db.create_all()  # Ensure tables exist

    # Check if vehicles already exist to avoid duplicates
    if Vehicle.query.count() == 0:
        for veh in sample_vehicles:
            new_vehicle = Vehicle(
                brand=veh["brand"],
                driver=veh["driver"],
                capacity=veh["capacity"],
                status=veh["status"],
            )
            db.session.add(new_vehicle)
        db.session.commit()
        print("Sample vehicles added to the database.")
    else:
        print("Database already has vehicles. Skipping insertion.")
