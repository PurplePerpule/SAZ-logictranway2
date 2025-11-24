import os
from itertools import permutations
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from typing import List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity # pyright: ignore[reportMissingImports]
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

app.config["JWT_SECRET_KEY"] = "your_secret_key_here"  # Замени на случайный ключ (e.g., os.urandom(32))
jwt = JWTManager(app)

# Configure SQLAlchemy
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    basedir, "database.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


order_cargo = db.Table(
    "order_cargo",
    db.Column("order_id", db.Integer, db.ForeignKey("order.id"), primary_key=True),
    db.Column("cargo_id", db.Integer, db.ForeignKey("cargo.id"), primary_key=True),
)

# Models
class Cargo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    length = db.Column(db.Float, nullable=False)
    width = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    departure = db.Column(db.String(200), nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    height = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "weight": self.weight,
            "length": self.length,
            "width": self.width,
            "quantity": self.quantity,
            "departure": self.departure,
            "destination": self.destination,
            "height": self.height,
        }


# fdfdfg kglf 'dflg' ' df' dfglmdms,dmv,c,x.v/ bbgf


class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    garage_number = db.Column(db.Integer, nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    driver = db.Column(db.String(100), nullable=False)
    gos_number = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Float, nullable=False)  # in kg
    length = db.Column(db.Float, nullable=False)  # in meters
    width = db.Column(db.Float, nullable=False)  # in meters
    height = db.Column(db.Float, nullable=False)  # in meters
    status = db.Column(
        db.String(50), nullable=False, default="free"
    )  # 'free' or 'busy'

    def to_dict(self):
        return {
            "id": self.id,
            "garage_number": self.garage_number,
            "brand": self.brand,
            "driver": self.driver,
            "gos_number": self.gos_number,
            "capacity": self.capacity,
            "length": self.length,
            "width": self.width,
            "height": self.height,
            "status": self.status,
        }

class Order(db.Model):
    __tablename__ = "order"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))
    status: Mapped[str] = mapped_column(default="new")
    vehicle_id: Mapped[int | None] = mapped_column(db.ForeignKey("vehicle.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(db.Text, nullable=True)

    vehicle: Mapped["Vehicle"] = relationship("Vehicle", backref="orders")
    cargos: Mapped[List["Cargo"]] = relationship(
        "Cargo",
        secondary=order_cargo,
        backref="orders",
        lazy="joined"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "vehicle_id": self.vehicle_id,
            "vehicle": self.vehicle.to_dict() if self.vehicle else None,
            "cargos": [c.to_dict() for c in self.cargos],
            "note": self.note,
        }

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    started_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="in_progress")

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
        }

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # "user" or "admin"

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "password": self.password,
            "role": self.role
        }




# API Routes


# Роут для логина
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data["username"]).first()
    if not user or not check_password_hash(user.password, data["password"]):
        return jsonify({"error": "Неверный логин или пароль"}), 401

    token = create_access_token(identity={"username": user.username, "role": user.role})
    return jsonify({"token": token, "role": user.role})

# Защита роутов
def role_required(role):
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorator(*args, **kwargs):
            current_user = get_jwt_identity()
            if current_user["role"] != role:
                return jsonify({"error": "Доступ запрещён"}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper



# Cargos
@app.route("/cargos", methods=["GET"])
def get_cargos():
    cargos = Cargo.query.all()
    return jsonify([cargo.to_dict() for cargo in cargos])


@app.route("/cargos", methods=["POST"])
def add_cargo():
    data = request.get_json()
    new_cargo = Cargo(**data)
    db.session.add(new_cargo)
    db.session.commit()
    return jsonify(new_cargo.to_dict()), 201


@app.route("/cargos/<int:id>", methods=["DELETE"])
def delete_cargo(id):
    cargo = Cargo.query.get_or_404(id)
    db.session.delete(cargo)
    db.session.commit()
    return jsonify({"message": "Cargo deleted"}), 200

# Vehicles
@app.route("/vehicles", methods=["GET"])
def get_vehicles():
    vehicles = Vehicle.query.all()
    return jsonify([vehicle.to_dict() for vehicle in vehicles])

@app.route("/vehicles", methods=["POST"])
def add_vehicle():
    data = request.get_json()
    new_vehicle = Vehicle(**data)
    db.session.add(new_vehicle)
    db.session.commit()
    return jsonify(new_vehicle.to_dict()), 201

@app.route("/vehicles/<int:id>", methods=["PUT", "PATCH"])
def update_vehicle_status(id):
    vehicle = Vehicle.query.get_or_404(id)
    data = request.get_json()
    if "status" in data:
        vehicle.status = data["status"]
        db.session.commit()
        return jsonify(vehicle.to_dict()), 200
    return jsonify({"error": "Status not provided"}), 400

# Orders
@app.route("/orders", methods=["GET"])
def get_orders():
    orders = Order.query.all()
    return jsonify([o.to_dict() for o in orders])

@app.route("/orders", methods=["POST"])
def add_order():
    data = request.get_json()
    cargos_data = data.get("cargos", [])

    order = Order()
    order.status = "new"
    db.session.add(order)
    db.session.flush()  # Чтобы получить ID

    for c_data in cargos_data:
        c_data.pop("id", None)
        cargo = Cargo(**c_data)
        db.session.add(cargo)
        db.session.flush()
        order.cargos.append(cargo)

    db.session.commit()
    return jsonify(order.to_dict()), 201

@app.route("/orders/<int:id>", methods=["GET"])
def get_order(id):
    order = Order.query.get_or_404(id)
    return jsonify(order.to_dict())

@app.route("/orders/<int:id>/assign", methods=["POST"])
def assign_vehicle(id):
    order = Order.query.get_or_404(id)
    data = request.get_json()
    vehicle_id = data.get("vehicle_id")

    vehicle = Vehicle.query.get_or_404(vehicle_id)
    if vehicle.status != "free":
        return jsonify({"error": "Машина занята"}), 400

    order.vehicle_id = vehicle_id
    order.status = "assigned"
    vehicle.status = "busy"
    vehicle.current_cargo_ids = ",".join(map(str, [c.id for c in order.cargos]))
    db.session.commit()

    return jsonify({"message": "Машина назначена"})

@app.route("/orders/<int:id>/complete", methods=["POST"])
def complete_order(id):
    order = Order.query.get_or_404(id)
    if order.status != "assigned":
        return jsonify({"error": "Рейс не назначен"}), 400

    order.status = "completed"
    order.vehicle.status = "free"
    order.vehicle.current_cargo_ids = None

    db.session.commit()
    return jsonify({"message": "Рейс завершён"})

# Suggest Vehicle (подбор для админки)
@app.route("/suggest_vehicle/<int:order_id>", methods=["GET"])
def suggest_vehicle(order_id):
    order = Order.query.get_or_404(order_id)
    cargos = order.cargos

    # Твой алгоритм подбора
    cargo_list = [c.to_dict() for c in cargos]
    total_weight = sum(c["weight"] * c["quantity"] for c in cargo_list)
    max_l = max(c["length"] for c in cargo_list)
    max_w = max(c["width"] for c in cargo_list)
    max_h_single = max(c["height"] for c in cargo_list)

    def can_stack_in_height(cargos, v_height):
        heights = sorted([c["height"] * c["quantity"] for c in cargos], reverse=True)
        total_stacked = 0
        for h in heights:
            if total_stacked + h <= v_height:
                total_stacked += h
            else:
                return False
        return True

    vehicles = Vehicle.query.filter_by(status="free").all()
    best = None
    min_extra = float("inf")

    for v in vehicles:
        if (v.capacity >= total_weight and v.length >= max_l and v.width >= max_w and (v.height >= max_h_single or can_stack_in_height(cargo_list, v.height))):
            extra = v.capacity - total_weight
            if extra < min_extra:
                min_extra = extra
                best = v

    if best:
        return jsonify(best.to_dict())
    return jsonify({"error": "Подходящая машина не найдена"}), 404

# Match (podbor mashiny)
@app.route("/match", methods=["POST"])
def match_vehicle():
    data = request.get_json()
    cargo_inputs = data.get("cargos", [])

    if not cargo_inputs:
        return jsonify({"message": "No cargos provided"}), 400

    # Если передали ID грузов — подгрузим из БД
    cargos = []
    for item in cargo_inputs:
        if isinstance(item, int):
            cargo = Cargo.query.get_or_404(item)
            cargos.append(cargo)
        else:
            cargos.append(item)

    cargo_list = []
    for c in cargos:
        if isinstance(c, dict):
            cargo_list.append(c)
        else:
            cargo_list.append(c.to_dict())

    if not cargo_list:
        return jsonify({"message": "No valid cargos"}), 400

    # Общий вес
    total_weight = sum(c["weight"] * c["quantity"] for c in cargo_list)

    # Максимальные габариты одного груза
    max_l = max(c["length"] for c in cargo_list)
    max_w = max(c["width"] for c in cargo_list)
    max_h_single = max(c["height"] for c in cargo_list)

    # Функция: можно ли уложить все грузы по высоте в данный кузов?
    def can_stack_in_height(cargos, vehicle_height):
        heights = sorted([c["height"] * c["quantity"] for c in cargos], reverse=True)

        total_stacked_height = 0
        for h in heights:
            if total_stacked_height + h <= vehicle_height:
                total_stacked_height += h
            else:
                if h > vehicle_height:
                    return False
                # В реальности можно ставить в несколько рядов по ширине/длине,
                # но для простоты: если не влез по высоте в один столб — считаем, что нельзя
                return False
        return total_stacked_height <= vehicle_height

    # Более точный вариант: попробовать все возможные порядки укладки (для малого количества — ок)
    def can_fit_by_height_precise(cargos, vehicle_height):
        items = []
        for c in cargos:
            items.extend([c["height"]] * c["quantity"])  # разворачиваем количество

        if not items:
            return True

        if max(items) > vehicle_height:
            return False
        if len(items) > 10:
            # Для большого количества используем жадный метод
            return (
                sum(sorted(items, reverse=True)) <= vehicle_height * 2
            )  # грубо, но безопасно

        for perm in permutations(items):
            stack = 0
            for h in perm:
                if stack + h > vehicle_height:
                    break
                stack += h
            else:
                if stack <= vehicle_height:
                    return True
        return False

    # Основной поиск подходящей машины
    suitable_vehicles = Vehicle.query.filter(
        Vehicle.status == "free",
        Vehicle.capacity >= total_weight,
        Vehicle.length >= max_l,
        Vehicle.width >= max_w,
    ).all()

    best_vehicle = None
    min_extra_capacity = float("inf")

    for vehicle in suitable_vehicles:
        v_height = vehicle.height

        # Вариант 1: без штабелирования (самый строгий)
        if v_height >= max_h_single:
            if vehicle.capacity - total_weight < min_extra_capacity:
                min_extra_capacity = vehicle.capacity - total_weight
                best_vehicle = vehicle
            continue  # этот точно подходит

        # Вариант 2: с штабелированием — проверяем, влезет ли по высоте
        if can_stack_in_height(cargo_list, v_height):
            if vehicle.capacity - total_weight < min_extra_capacity:
                min_extra_capacity = vehicle.capacity - total_weight
                best_vehicle = vehicle

    if best_vehicle:
        return jsonify(
            {
                "message": "Suitable vehicle found",
                "vehicle": best_vehicle.to_dict(),
                "total_weight": total_weight,
                "required_dimensions": {
                    "length": max_l,
                    "width": max_w,
                    "height_strategy": "stacked"
                    if best_vehicle.height < max_h_single
                    else "no_stacking",
                },
                "note": "Грузы можно штабелировать по высоте"
                if best_vehicle.height < max_h_single
                else "Штабелирование не требуется",
            }
        )

    return jsonify(
        {
            "message": "No suitable vehicle found",
            "required": {
                "weight": total_weight,
                "length": max_l,
                "width": max_w,
                "height_single": max_h_single,
                "height_stacked_estimate": sum(
                    c["height"] * c["quantity"] for c in cargo_list
                ),
            },
        }
    ), 404

@app.route("/ttn/<int:order_id>", methods=["GET"])
def generate_ttn(order_id):
    order = Order.query.get_or_404(order_id)
    ttn_data = {
        "ttn_number": f"TTN-{order.id:06d}",
        "date": datetime.now().strftime("%d.%m.%Y"),
        "driver": order.vehicle.driver,
        "gos_number": order.vehicle.gos_number,
        "cargos": [c.to_dict() for c in order.cargos],
        "total_weight": sum(c.weight * c.quantity for c in order.cargos)
    }
    return jsonify(ttn_data)

if __name__ == "__main__":
    with app.app_context():
        if not User.query.first():
            user = User(username="user", password=generate_password_hash("sazwork205"), role="user")
            admin = User(username="admin", password=generate_password_hash("sazadmin2025"), role="admin")
            db.session.add(user)
            db.session.add(admin)
            db.session.commit()
        db.create_all()
    app.run(debug=True, port=5000)
