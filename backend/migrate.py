from app import app, db, Order, Trip
from datetime import datetime, timezone

with app.app_context():
    # Находим все назначенные или завершенные заявки без рейсов
    orders_without_trips = Order.query.filter(
        Order.status.in_(["assigned", "completed"]),
        Order.vehicle_id.isnot(None)
    ).all()

    print(f"Найдено {len(orders_without_trips)} заявок без рейсов")

    for order in orders_without_trips:
        # Проверяем, нет ли уже рейса для этой заявки
        existing_trip = Trip.query.filter_by(order_id=order.id).first()
        if not existing_trip:
            trip = Trip(
                order_id=order.id,
                vehicle_id=order.vehicle_id,
                started_at=order.created_at,
                status="completed" if order.status == "completed" else "in_progress",
                completed_at=datetime.now(timezone.utc) if order.status == "completed" else None,
                distance_km=100.0,  # Примерные данные
                fuel_consumed=25.0,
                notes="Создано автоматически при миграции"
            )
            db.session.add(trip)
            print(f"Создан рейс для заявки #{order.id}")

    db.session.commit()
    print(f"Миграция завершена. Всего рейсов: {Trip.query.count()}")
