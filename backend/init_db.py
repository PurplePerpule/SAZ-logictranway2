from app import Vehicle, app, db

# Sample vehicles data
sample_vehicles = [
    {
        "brand": "Ford Transit",
        "driver": "John Doe",
        "capacity": 1500.0,  # in kg
        "status": "free",
    },
    {
        "brand": "Mercedes Sprinter",
        "driver": "Jane Smith",
        "capacity": 2000.0,
        "status": "free",
    },
    {
        "brand": "Volkswagen Crafter",
        "driver": "Alex Johnson",
        "capacity": 3000.0,
        "status": "busy",
    },
    {
        "brand": "Iveco Daily",
        "driver": "Emily Davis",
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
