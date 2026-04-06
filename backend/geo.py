from app import app, db, Location
from app import geocode_address

with app.app_context():
    locations = Location.query.filter(
        (Location.latitude == None) | (Location.longitude == None)
    ).all()
    print(f"Найдено адресов без координат: {len(locations)}")
    for loc in locations:
        coords = geocode_address(loc.address)
        if coords:
            lat, lon = coords
            loc.latitude = lat
            loc.longitude = lon
            print(f"✓ {loc.address} -> {lat}, {lon}")
        else:
            print(f"✗ Не удалось геокодировать: {loc.address}")
    db.session.commit()
    print("Готово")
