from app import app, db, Order, Trip
from datetime import datetime, timezone, timedelta

with app.app_context():
    # Находим заявки, которые назначены или завершены
    orders = Order.query.filter(Order.status.in_(["assigned", "completed"])).all()

    print(f"Найдено {len(orders)} заявок для создания рейсов")

    for i, order in enumerate(orders, 1):
        # Проверяем, нет ли уже рейса для этой заявки
        existing_trip = Trip.query.filter_by(order_id=order.id).first()
        if not existing_trip:
            trip = Trip(
                order_id=order.id,
                vehicle_id=order.vehicle_id,
                started_at=order.created_at,
                status="completed" if order.status == "completed" else "in_progress",
                completed_at=datetime.now(timezone.utc) if order.status == "completed" else None,
                distance_km=100.5 + i * 10,  # Тестовые данные
                fuel_consumed=30.2 + i * 2
            )
            db.session.add(trip)
            print(f"Создан рейс для заявки #{order.id}")

    db.session.commit()
    print("Рейсы созданы!")
