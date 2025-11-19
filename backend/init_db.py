from app import Vehicle, app, db

# Sample vehicles data
sample_vehicles = [
    {
        "garage_number": "1",
        "brand": "ГАЗ 3302",
        "driver": "Гуринович А.В.",
        "gos_number": "АВ 6101-4",
        "capacity": 1500.0,  # kg
        "length": 3.0,  # m
        "width": 2.2,
        "height": 1.750,
        "status": "free",
    },
    {
        "garage_number": "7",
        "brand": "ГАЗ 3302",
        "driver": "Клевцов Ю.В.",
        "gos_number": "АВ 6100-4",
        "capacity": 1500.0,
        "length": 3.0,
        "width": 2.2,
        "height": 1.750,
        "status": "free",
    },
    {
        "garage_number": "8",
        "brand": "ГАЗ А22 R23-50",
        "driver": "Докурно Р.М.",
        "gos_number": "АМ 7485-4",
        "capacity": 1500.0,
        "length": 2.0,
        "width": 2.2,
        "height": 1.750,
        "status": "free",
    },
    {
        "garage_number": "16",
        "brand": "МАЗ 4371",
        "driver": "Жданюк В.В.",
        "gos_number": "АВ 7555-4",
        "capacity": 5000.0,
        "length": 6.0,
        "width": 2.4,
        "height": 2.3,
        "status": "free",
    },
    {
        "garage_number": "17",
        "brand": "МАЗ 5440А5",
        "driver": "Гулецкий А.Э.",
        "gos_number": "АH 0425-4",
        "capacity": 20000.0,
        "length": 13.7,
        "width": 2.4,
        "height": 2.4,
        "status": "free",
    },
    {
        "garage_number": "12",
        "brand": "МАЗ 4370",
        "driver": "Кособутский В.А.",
        "gos_number": "7349 АВ-4",
        "capacity": 5000.0,
        "length": 6.0,
        "width": 2.4,
        "height": 2.2,
        "status": "free",
    },
    {
        "garage_number": "290",
        "brand": "МАЗ 5340 В5",  # У машины есть прицеп
        "driver": "Вишняк И.И.",
        "gos_number": "АК 4925-4",
        "capacity": 20000.0,
        "length": 6.0,
        "width": 2.4,
        "height": 0.6,
        "status": "free",
    },
    {
        "garage_number": "32",  # САМОСВАЛ ВОЗМОЖНО НЕ НУЖЕН
        "brand": "МАЗ 5440С9",
        "driver": "Граматовский В.И.",
        "gos_number": "АМ 9310-4",
        "capacity": 20000.0,
        "length": 13.7,
        "width": 2.4,
        "height": 2.4,
        "status": "free",
    },
    {
        "garage_number": "34",
        "brand": "МАЗ 544028",
        "driver": "Клакевич И.Н.",
        "gos_number": "АМ 9397-4",
        "capacity": 20000.0,
        "length": 13.7,
        "width": 2.4,
        "height": 2.4,
        "status": "free",
    },
    {
        "garage_number": "35",
        "brand": "ГАЗ А31 R32",
        "driver": "Воронович С.Ч.",
        "gos_number": "АН 5280-4",
        "capacity": 1100.0,
        "length": 3.6,
        "width": 1.8,
        "height": 1.9,
        "status": "free",
    },
    {
        "garage_number": "37",
        "brand": "МАЗ 4371",
        "driver": "Мартусевич Д.Е.",
        "gos_number": "AI 9499-4",
        "capacity": 5000.0,
        "length": 6.0,
        "width": 2.4,
        "height": 2.3,
        "status": "free",
    },
    {
        "garage_number": "39",
        "brand": "МАЗ 5440А8",
        "driver": "Лисовский А.Э.",
        "gos_number": "AA 8218-4",
        "capacity": 20000.0,
        "length": 13.7,
        "width": 2.4,
        "height": 0.5,
        "status": "free",
    },
    {
        "garage_number": "40",
        "brand": "МАЗ 5440С9",
        "driver": "Кохановский В.З.",
        "gos_number": "АН 7177-4",
        "capacity": 20000.0,
        "length": 13.7,
        "width": 2.4,
        "height": 0.6,  # открытая
        "status": "free",
    },
    {
        "garage_number": "60",
        "brand": "МАЗ 5340B5",  # У этой машины есть прицеп
        "driver": "Нет водителя",
        "gos_number": "АI 9623-4",
        "capacity": 9000.0,
        "length": 6.0,
        "width": 2.4,
        "height": 2.4,
        "status": "free",
    },
    {
        "garage_number": "60",
        "brand": "ГАЗ 2218",
        "driver": "Станкевич И.В.",
        "gos_number": "АB 7878-4",
        "capacity": 3000.0,
        "length": 4.0,
        "width": 2.4,
        "height": 2.2,
        "status": "free",
    },
    {
        "garage_number": "60",
        "brand": "МАЗ 543205",
        "driver": "Медовский И.М.",
        "gos_number": "АI 2592-4",
        "capacity": 20000.0,
        "length": 13.7,
        "width": 2.4,
        "height": 0.5,
        "status": "free",
    },
]

with app.app_context():
    db.create_all()

    if Vehicle.query.count() == 0:
        for veh in sample_vehicles:
            new_vehicle = Vehicle(
                garage_number=veh["garage_number"],
                brand=veh["brand"],
                driver=veh["driver"],
                gos_number=veh["gos_number"],
                capacity=veh["capacity"],
                length=veh["length"],
                width=veh["width"],
                height=veh["height"],
                status=veh["status"],
            )
            db.session.add(new_vehicle)
        db.session.commit()
        print("Sample vehicles added to the database.")
    else:
        print("Database already has vehicles. Skipping insertion.")
