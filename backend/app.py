from itertools import permutations
from datetime import datetime, timezone, timedelta, time
from flask import Flask, jsonify, request, send_file, make_response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from typing import List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from io import BytesIO
from openpyxl.workbook.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from threading import Thread

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pdfkit

import os


app = Flask(__name__)
CORS(app)


app.config["SECRET_KEY"] = "c639183901c409352be3d01c521c7694"

login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=1)  # Сессия на 1 час
app.config["SESSION_COOKIE_SECURE"] = True  # Только для HTTPS
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "database.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

order_cargo = db.Table(
    "order_cargo",
    db.Column("order_id", db.Integer, db.ForeignKey("order.id"), primary_key=True),
    db.Column("cargo_id", db.Integer, db.ForeignKey("cargo.id"), primary_key=True),
)


class Cargo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    length = db.Column(db.Float, nullable=True)  # Делаем nullable
    width = db.Column(db.Float, nullable=True)   # Делаем nullable
    height = db.Column(db.Float, nullable=True)  # Делаем nullable
    volume = db.Column(db.Float, nullable=True)  # НОВОЕ: объем груза в м³
    quantity = db.Column(db.Integer, nullable=False)
    departure = db.Column(db.String(200), nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    tent_type = db.Column(db.String(20), nullable=False, default="closed")
    cargo_type = db.Column(db.String(20), nullable=False, default="dimensions")  # НОВОЕ: тип груза - "dimensions" или "volume"

    # Добавьте это отношение
    orders = relationship("Order", secondary=order_cargo, back_populates="cargos")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "weight": self.weight,
            "length": self.length,
            "width": self.width,
            "height": self.height,
            "volume": self.volume,  # НОВОЕ
            "quantity": self.quantity,
            "departure": self.departure,
            "destination": self.destination,
            "tent_type": self.tent_type,
            "cargo_type": self.cargo_type,  # НОВОЕ
        }

class DraftCargo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    length = db.Column(db.Float, nullable=True)  # Делаем nullable
    width = db.Column(db.Float, nullable=True)   # Делаем nullable
    height = db.Column(db.Float, nullable=True)  # Делаем nullable
    volume = db.Column(db.Float, nullable=True)  # НОВОЕ: объем груза в м³
    quantity = db.Column(db.Integer, nullable=False)
    departure = db.Column(db.String(200), nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tent_type = db.Column(db.String(20), nullable=False, default="closed")
    cargo_type = db.Column(db.String(20), nullable=False, default="dimensions")  # НОВОЕ

    # Добавьте это отношение
    user = relationship("User", back_populates="draft_cargos")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "weight": self.weight,
            "length": self.length,
            "width": self.width,
            "height": self.height,
            "volume": self.volume,  # НОВОЕ
            "quantity": self.quantity,
            "departure": self.departure,
            "destination": self.destination,
            "tent_type": self.tent_type,
            "cargo_type": self.cargo_type,  # НОВОЕ
        }





class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    garage_number = db.Column(db.Integer, nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    driver = db.Column(db.String(100), nullable=False)
    gos_number = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Float, nullable=False)
    length = db.Column(db.Float, nullable=False)
    width = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default="free")
    tent_type = db.Column(db.String(20), nullable=False, default="closed")

    # Добавьте это отношение
    orders = relationship("Order", back_populates="vehicle")

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
            "tent_type": self.tent_type,
        }

class Order(db.Model):
    __tablename__ = "order"
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))
    status: Mapped[str] = mapped_column(default="new")
    vehicle_id: Mapped[int | None] = mapped_column(db.ForeignKey("vehicle.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(db.Text, nullable=True)
    applicant = db.Column(db.String(100), nullable=False, default="Не указан")
    department = db.Column(db.String(100), nullable=False, default="Не указан")
    phone_number = db.Column(db.String(20), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    preferred_departure_date = db.Column(db.Date, nullable=True)
    priority = db.Column(db.String(20), default="normal")  # НОВОЕ: high, normal, low

    # Добавьте эти отношения
    cargos = relationship("Cargo", secondary=order_cargo, back_populates="orders")
    vehicle = relationship("Vehicle", back_populates="orders")
    user = relationship("User", back_populates="orders")

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "vehicle_id": self.vehicle_id,
            "vehicle": self.vehicle.to_dict() if self.vehicle else None,
            "cargos": [c.to_dict() for c in self.cargos],
            "note": self.note,
            "applicant": self.applicant,
            "department": self.department,
            "phone_number": self.phone_number,
            "preferred_departure_date": self.preferred_departure_date.isoformat() if self.preferred_departure_date else None,
            "user_id": self.user_id,
            "priority": self.priority,
        }

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'))
    started_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="in_progress")
    distance_km = db.Column(db.Float, nullable=True)  # километраж
    fuel_consumed = db.Column(db.Float, nullable=True)  # расход топлива
    notes = db.Column(db.Text, nullable=True)  # заметки водителя

    # Добавляем отношения
    order = relationship("Order", backref="trips")
    vehicle = relationship("Vehicle", backref="trips")

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "vehicle_id": self.vehicle_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "distance_km": self.distance_km,
            "fuel_consumed": self.fuel_consumed,
            "notes": self.notes
        }


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    full_name = db.Column(db.String(100), nullable=True)
    department = db.Column(db.String(100), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)

    # Добавьте это отношение
    orders = relationship("Order", back_populates="user")
    draft_cargos = relationship("DraftCargo", back_populates="user")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "password": self.password,
            "role": self.role,
            "full_name": self.full_name,
            "department": self.department,
            "phone_number": self.phone_number,
        }


def role_required(role):

    def wrapper(fn):

        @wraps(fn)

        @login_required
        def decorator(*args, **kwargs):

            if not current_user.is_authenticated or current_user.role != role:
                return jsonify({"error": "Доступ запрещён"}), 403

            return fn(*args, **kwargs)

        return decorator

    return wrapper

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

        if not token:
            return jsonify({'error': 'Требуется авторизация'}), 401

        try:
            # Вместо JWT используем проверку через Flask-Login
            if not current_user.is_authenticated:
                return jsonify({'error': 'Неверный токен'}), 401
        except:
            return jsonify({'error': 'Неверный токен'}), 401

        return f(*args, **kwargs)
    return decorated

@app.route("/login", methods=["POST"])

def login():

    data = request.get_json() or {}

    user = User.query.filter_by(username=data.get("username")).first()

    if not user or not check_password_hash(user.password, data.get("password", "")):
        return jsonify({"error": "Неверный логин или пароль"}), 401

    login_user(user)
    # Возвращаем "token" для обратной совместимости с фронтом
    return jsonify({"token": "ok", "role": user.role})

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Вышли из системы"})

# Регистрация нового пользователя (только для админа)
@app.route("/register", methods=["POST"])
@login_required
@role_required("admin")
def register_user():
    data = request.get_json()

    if User.query.filter_by(username=data.get("username")).first():
        return jsonify({"error": "Пользователь с таким логином уже существует"}), 400

    new_user = User(
        username=data["username"],
        password=generate_password_hash(data["password"]),
        role=data.get("role", "user"),
        full_name=data.get("full_name"),
        department=data.get("department"),
        phone_number=data.get("phone_number")
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "Пользователь создан",
        "user": new_user.to_dict()
    }), 201

# Получение списка пользователей (только для админа)
@app.route("/users", methods=["GET"])
@login_required
@role_required("admin")
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

# Получение данных текущего пользователя
@app.route("/me", methods=["GET"])
@login_required
def get_current_user():
    return jsonify(current_user.to_dict())

# Обновление данных пользователя
@app.route("/users/<int:user_id>", methods=["PUT"])
@login_required
def update_user(user_id):
    # Пользователь может редактировать только себя, админ - любого
    if current_user.id != user_id and current_user.role != "admin":
        return jsonify({"error": "Доступ запрещён"}), 403

    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if "password" in data:
        user.password = generate_password_hash(data["password"])
    if "full_name" in data:
        user.full_name = data["full_name"]
    if "department" in data:
        user.department = data["department"]
    if "phone_number" in data:
        user.phone_number = data["phone_number"]

    db.session.commit()
    return jsonify(user.to_dict())

# Удаление пользователя (только для админа)
@app.route("/users/<int:user_id>", methods=["DELETE"])
@login_required
@role_required("admin")
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        return jsonify({"error": "Нельзя удалить самого себя"}), 400

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Пользователь удалён"}), 200


#@app.route("/cargos", methods=["GET"])
#def get_cargos():
#    cargos = Cargo.query.all()
#    return jsonify([cargo.to_dict() for cargo in cargos])


#@app.route("/cargos", methods=["POST"])
#def add_cargo():
#    data = request.get_json()
#    new_cargo = Cargo(**data)
#    db.session.add(new_cargo)
#    db.session.commit()
#    return jsonify(new_cargo.to_dict()), 201

#@app.route("/cargos/<int:id>", methods=["DELETE"])
#def delete_cargo(id):
#    cargo = Cargo.query.get_or_404(id)
#    db.session.delete(cargo)
#    db.session.commit()
#    return jsonify({"message": "Cargo deleted"}), 200



@app.route("/vehicles", methods=["GET"])
def get_vehicles():
    vehicles = Vehicle.query.all()
    return jsonify([vehicle.to_dict() for vehicle in vehicles])

@app.route("/vehicles/<int:vehicle_id>", methods=["GET"])
def get_vehicle_by_id(vehicle_id):
    """Получение данных конкретного автомобиля по ID"""
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    return jsonify(vehicle.to_dict())

@app.route("/vehicles", methods=["POST"])
def add_vehicle():
    data = request.get_json()
    new_vehicle = Vehicle(**data)
    db.session.add(new_vehicle)
    db.session.commit()
    return jsonify(new_vehicle.to_dict()), 201


@app.route("/vehicles/<int:id>", methods=["PUT", "PATCH"])

@login_required
def update_vehicle_status(id):

    if not current_user.is_authenticated or current_user.role != "admin":
        return jsonify({"error": "Только администратор"}), 403
    vehicle = Vehicle.query.get_or_404(id)

    data = request.get_json()

    if "status" in data:

        vehicle.status = data["status"]

        db.session.commit()

        return jsonify(vehicle.to_dict()), 200

    return jsonify({"error": "Status not provided"}), 400


@app.route("/orders", methods=["GET"])
@login_required
def get_orders():
    if current_user.role == "admin":
        # Админ видит все заявки
        orders = Order.query.all()
    else:
        # Пользователь видит только свои заявки
        orders = Order.query.filter_by(user_id=current_user.id).all()

    # Преобразуем в словари с правильными данными о машине
    orders_data = []
    for order in orders:
        order_dict = order.to_dict()
        # Убедимся, что vehicle существует и не None
        if order.vehicle:
            order_dict["vehicle"] = order.vehicle.to_dict()
        else:
            order_dict["vehicle"] = None
        orders_data.append(order_dict)

    return jsonify(orders_data)

@app.route("/orders/<int:order_id>", methods=["GET"])
def get_order_by_id(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify(order.to_dict())

@app.route("/orders", methods=["POST"])
@login_required
def add_order():
    local_tz = timezone(timedelta(hours=3))
    now_local = datetime.now(local_tz)

    if now_local.time() >= time(18, 0):
        return jsonify({
            "error": "Заявки принимаются только до 12:30. "
                     "Пожалуйста, отправьте заявку завтра до 12:30."
        }), 403

    data = request.get_json()

    print(f"[DEBUG add_order] Полученные данные: {data}")
    print(f"[DEBUG add_order] preferred_departure_date: {data.get('preferred_departure_date')}")

    applicant = data.get("applicant") or current_user.full_name or "Не указан"
    department = data.get("department") or current_user.department or "Не указан"
    phone_number = data.get("phone_number") or current_user.phone_number

    draft_cargos = DraftCargo.query.filter_by(user_id=current_user.id).all()

    if not draft_cargos:
        return jsonify({"error": "Нет грузов в заявке"}), 400

    # Обрабатываем желаемую ДАТУ отправления (ВМЕСТО времени)
    preferred_departure_date = None
    if data.get("preferred_departure_date"):
        try:
            date_str = data["preferred_departure_date"]
            # Преобразуем строку в дату (формат YYYY-MM-DD)
            preferred_departure_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception as e:
            return jsonify({"error": f"Неверный формат даты: {str(e)}"}), 400

    # Создаём заявку с привязкой к пользователю
    order = Order(
        applicant=applicant,
        department=department,
        phone_number=phone_number,
        status="new",
        user_id=current_user.id,
        preferred_departure_date=preferred_departure_date  # Используем новое поле
    )
    db.session.add(order)
    db.session.flush()

    # Копируем грузы из черновика текущего пользователя
    for draft in draft_cargos:
        cargo = Cargo(
            name=draft.name,
            weight=draft.weight,
            length=draft.length,
            width=draft.width,
            height=draft.height,
            volume=draft.volume,  # НОВОЕ: копируем объем
            quantity=draft.quantity,
            departure=draft.departure,
            destination=draft.destination,
            tent_type=draft.tent_type,
            cargo_type=draft.cargo_type  # НОВОЕ: копируем тип груза
        )
        db.session.add(cargo)
        db.session.flush()
        order.cargos.append(cargo)

    # Очищаем черновик текущего пользователя
    DraftCargo.query.filter_by(user_id=current_user.id).delete()

    db.session.commit()
    return jsonify(order.to_dict()), 201

@app.route("/draft_cargos", methods=["GET"])
@login_required
def get_draft_cargos():
    cargos = DraftCargo.query.filter_by(user_id=current_user.id).all()
    return jsonify([c.to_dict() for c in cargos])

@app.route("/draft_cargos", methods=["POST"])
@login_required
def add_draft_cargo():
    data = request.get_json()
    print(f"[DEBUG] Received draft cargo data: {data}")  # Для отладки

    cargo = DraftCargo(
        name=data.get("name"),
        weight=data.get("weight"),
        length=data.get("length"),
        width=data.get("width"),
        height=data.get("height"),
        volume=data.get("volume"),  # НОВОЕ: принимаем объем
        quantity=data.get("quantity"),
        departure=data.get("departure"),
        destination=data.get("destination"),
        tent_type=data.get("tent_type", "closed"),
        cargo_type=data.get("cargo_type", "dimensions"),  # НОВОЕ: принимаем тип груза
        user_id=current_user.id
    )
    db.session.add(cargo)
    db.session.commit()
    return jsonify(cargo.to_dict()), 201

@app.route("/draft_cargos/<int:id>", methods=["DELETE"])
@login_required
def delete_draft_cargo(id):
    cargo = DraftCargo.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(cargo)
    db.session.commit()
    return jsonify({"message": "Удалено"})

@app.route("/draft_cargos/clear", methods=["DELETE"])
@login_required
def clear_draft_cargos():
    DraftCargo.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({"message": "Черновик очищен"})


@app.route("/orders/<int:id>/assign", methods=["POST"])
def assign_vehicle(id):
    order = Order.query.get_or_404(id)
    data = request.get_json()
    vehicle_id = data.get("vehicle_id")
    vehicle = Vehicle.query.get_or_404(vehicle_id)

    if vehicle.status == "in_repair":
        return jsonify({"error": "Машина в ремонте"}), 400
    if vehicle.status != "free":
        return jsonify({"error": "Машина занята"}), 400

    order.vehicle_id = vehicle_id
    order.status = "assigned"
    vehicle.status = "busy"

    # АВТОМАТИЧЕСКОЕ СОЗДАНИЕ РЕЙСА ПРИ НАЗНАЧЕНИИ МАШИНЫ
    trip = Trip(
        order_id=order.id,
        vehicle_id=vehicle_id,
        started_at=datetime.now(timezone.utc),
        status="in_progress"
    )
    db.session.add(trip)

    db.session.commit()
    return jsonify({"message": "Машина назначена, рейс создан"})


@app.route("/orders/<int:id>/complete", methods=["POST"])
@login_required
def complete_order(id):
    order = Order.query.get_or_404(id)

    if order.status != "assigned":
        return jsonify({"error": "Рейс не назначен или уже завершен"}), 400

    # Находим рейс для этой заявки
    trip = Trip.query.filter_by(order_id=order.id).first()

    if not trip:
        # Если рейс не был создан (для старых данных), создаем его
        trip = Trip(
            order_id=order.id,
            vehicle_id=order.vehicle_id,
            started_at=order.created_at,
            status="completed",
            completed_at=datetime.now(timezone.utc)
        )
        db.session.add(trip)
    else:
        # Обновляем существующий рейс
        trip.status = "completed"
        trip.completed_at = datetime.now(timezone.utc)

    # Обновляем статус заявки
    order.status = "completed"

    # Освобождаем машину
    if order.vehicle:
        order.vehicle.status = "free"

    db.session.commit()
    return jsonify({"message": "Рейс завершён"})

@app.route("/suggest_vehicle/<int:order_id>", methods=["GET"])
def suggest_vehicle(order_id):
    order = Order.query.get_or_404(order_id)
    cargos = order.cargos
    if not cargos:
        return jsonify({"error": "В заявке нет грузов"}), 404

    cargo_list = [c.to_dict() for c in cargos]

    # Проверяем, есть ли грузы с разными типами тента
    tent_types = set(c.get("tent_type", "closed") for c in cargo_list)
    if len(tent_types) > 1:
        return jsonify({"error": f"В заявке грузы с разными типами тента: {', '.join(tent_types)}. Невозможно подобрать одну машину."}), 400

    required_tent_type = cargo_list[0].get("tent_type", "closed")

    total_weight = sum(c["weight"] * c["quantity"] for c in cargo_list)

    # Рассчитываем максимальные габариты ИЛИ общий объем
    max_l = 0
    max_w = 0
    max_h_single = 0
    total_volume = 0

    for c in cargo_list:
        if c.get("cargo_type") == "dimensions" and c.get("length") and c.get("width") and c.get("height"):
            # Груз с габаритами
            max_l = max(max_l, c["length"])
            max_w = max(max_w, c["width"])
            max_h_single = max(max_h_single, c["height"])
            total_volume += c["length"] * c["width"] * c["height"] * c["quantity"]
        elif c.get("cargo_type") == "volume" and c.get("volume"):
            # Груз с объемом
            total_volume += c["volume"] * c["quantity"]
            # Для объемных грузов не можем определить габариты, поэтому используем минимальные требования
            max_l = max(max_l, 0.1)  # Минимальная длина
            max_w = max(max_w, 0.1)  # Минимальная ширина
            max_h_single = max(max_h_single, 0.1)  # Минимальная высота

    print(f"[DEBUG] Order #{order_id} - required tent type: {required_tent_type}")
    print(f"[DEBUG] Total weight: {total_weight}, total volume: {total_volume}m³")

    def can_stack_in_height(cargos, v_height):
        heights = []
        for c in cargos:
            for _ in range(c["quantity"]):
                if c.get("cargo_type") == "dimensions" and c.get("height"):
                    heights.append(c["height"])
                else:
                    # Для объемных грузов считаем, что они занимают всю высоту
                    heights.append(v_height)
        heights.sort(reverse=True)
        return all(h <= v_height for h in heights)

    # Ищем машины с указанным типом тента
    vehicles = Vehicle.query.filter(
        Vehicle.status == "free",
        Vehicle.tent_type == required_tent_type,
        Vehicle.status != "in_repair"
    ).all()

    best = None
    min_extra = float("inf")
    suitable_vehicles = []

    for v in vehicles:
        # Проверка по весу
        if v.capacity < total_weight:
            print(f"[DEBUG] Vehicle {v.garage_number} failed weight check: {v.capacity} < {total_weight}")
            continue

        # Проверка по объему
        vehicle_volume = v.length * v.width * v.height
        if vehicle_volume < total_volume:
            print(f"[DEBUG] Vehicle {v.garage_number} failed volume check: {vehicle_volume}m³ < {total_volume}m³")
            continue

        # Проверка по минимальным габаритам
        if max_l > v.length or max_w > v.width:
            print(f"[DEBUG] Vehicle {v.garage_number} failed dimensions check: {v.length}x{v.width}m vs {max_l}x{max_w}m")
            continue

        # Проверка по высоте
        if v.height < max_h_single:
            if not can_stack_in_height(cargo_list, v.height):
                print(f"[DEBUG] Vehicle {v.garage_number} failed height check: {v.height} < {max_h_single}")
                continue

        # Машина подходит
        extra = v.capacity - total_weight
        suitable_vehicles.append(v)
        if extra < min_extra:
            min_extra = extra
            best = v
        print(f"[DEBUG] Vehicle {v.garage_number} is suitable (extra: {extra}kg)")

    if best:
        return jsonify(best.to_dict())

    print(f"[DEBUG] No suitable vehicles with tent_type='{required_tent_type}'. Searching all free vehicles...")

    # Если не нашли машину с нужным типом тента, ищем любую доступную
    all_vehicles = Vehicle.query.filter(
        Vehicle.status == "free",
        Vehicle.status != "in_repair"
    ).all()

    for v in all_vehicles:
        if (v.capacity >= total_weight):
            vehicle_volume = v.length * v.width * v.height
            if vehicle_volume >= total_volume:
                # Проверка по минимальным габаритам
                if not (max_l > v.length or max_w > v.width):
                    # Проверка по высоте
                    if v.height < max_h_single:
                        if not can_stack_in_height(cargo_list, v.height):
                            continue
                    extra = v.capacity - total_weight
                    suitable_vehicles.append(v)
                    if extra < min_extra:
                        min_extra = extra
                        best = v

    if best:
        return jsonify({
            "vehicle": best.to_dict(),
            "warning": f"Не найдена машина с типом тента '{required_tent_type}'. Предлагается машина с типом тента '{best.tent_type}'"
        })

    print(f"[DEBUG] No suitable vehicles at all")
    return jsonify({"error": f"Подходящая машина не найдена. Требования: {total_weight}кг, {total_volume}м³"}), 404


from app import app, db, Order, Trip
from datetime import datetime, timezone, timedelta

with app.app_context():
    # Сначала убедимся, что таблицы существуют
    db.create_all()

    # Затем выполняем миграцию
    orders = Order.query.filter(Order.status.in_(["assigned", "completed"])).all()

    if orders:
        print(f"Мигрируем {len(orders)} заявок в рейсы...")
        for i, order in enumerate(orders, 1):
            existing_trip = Trip.query.filter_by(order_id=order.id).first()
            if not existing_trip:
                trip = Trip(
                    order_id=order.id,
                    vehicle_id=order.vehicle_id,
                    started_at=order.created_at,
                    status="completed" if order.status == "completed" else "in_progress",
                    completed_at=datetime.now(timezone.utc) if order.status == "completed" else None,
                    distance_km=100.5 + i * 10,
                    fuel_consumed=30.2 + i * 2
                )
                db.session.add(trip)
        db.session.commit()
        print("Миграция завершена!")
    else:
        print("Нет заявок для миграции")

    @app.route("/complete_trip_with_data/<int:order_id>", methods=["POST"])
    @login_required
    @role_required("admin")
    def complete_trip_with_data(order_id):
        """Завершить рейс с данными о пробеге и топливе"""
        data = request.get_json()

        order = Order.query.get_or_404(order_id)
        trip = Trip.query.filter_by(order_id=order_id, status="in_progress").first()

        if not trip:
            return jsonify({"error": "Активный рейс не найден"}), 404

        trip.status = "completed"
        trip.completed_at = datetime.now(timezone.utc)
        trip.distance_km = data.get("distance_km")
        trip.fuel_consumed = data.get("fuel_consumed")
        trip.notes = data.get("notes")

        order.status = "completed"
        if order.vehicle:
            order.vehicle.status = "free"

        db.session.commit()
        return jsonify({"message": "Рейс завершен с данными", "trip": trip.to_dict()})



@app.route("/stats", methods=["GET"])
@login_required
def get_stats():
    orders = Order.query.all()

    pending = Order.query.filter_by(status="new").count()
    assigned = Order.query.filter_by(status="assigned").count()

    # Завершено сегодня
    today = datetime.now(timezone.utc).date()
    completed_today = Order.query.filter(
        Order.status == "completed",
        db.func.date(Order.created_at) == today
    ).count()

    return jsonify({
        "pending": pending,
        "assigned": assigned,
        "completed_today": completed_today
    })

@app.route("/match", methods=["POST"])
def match_vehicle():
    data = request.get_json()
    cargo_inputs = data.get("cargos", [])

    # Теперь tent_type определяется по грузам, а не передается отдельно
    print(f"[DEBUG] Match request: cargos={len(cargo_inputs)}")

    if not cargo_inputs:
        return jsonify({"message": "No cargos provided"}), 400

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

    # Проверяем тип тента грузов
    tent_types = set(c.get("tent_type", "closed") for c in cargo_list)
    if len(tent_types) > 1:
        return jsonify({
            "message": "Грузы имеют разные типы тента",
            "tent_types": list(tent_types)
        }), 400

    required_tent_type = list(tent_types)[0]

    total_weight = sum(c["weight"] * c["quantity"] for c in cargo_list)
    max_l = max(c["length"] for c in cargo_list)
    max_w = max(c["width"] for c in cargo_list)
    max_h_single = max(c["height"] for c in cargo_list)

    print(f"[DEBUG] Required tent type: {required_tent_type}")
    print(f"[DEBUG] Total weight: {total_weight}, max dimensions: {max_l}x{max_w}x{max_h_single}")

    def can_stack_in_height(cargos, vehicle_height):
        heights = []
        for c in cargos:
            for _ in range(c["quantity"]):
                heights.append(c["height"])
        heights.sort(reverse=True)
        return all(h <= vehicle_height for h in heights)

    # Сначала ищем машины с указанным типом тента
    suitable_vehicles = Vehicle.query.filter(
        Vehicle.status == "free",
        Vehicle.capacity >= total_weight,
        Vehicle.length >= max_l,
        Vehicle.width >= max_w,
        Vehicle.tent_type == required_tent_type,
        Vehicle.status != "in_repair"
    ).all()

    print(f"[DEBUG] Found {len(suitable_vehicles)} vehicles with tent_type='{required_tent_type}'")

    best_vehicle = None
    min_extra_capacity = float("inf")

    for vehicle in suitable_vehicles:
        v_height = vehicle.height
        if v_height >= max_h_single:
            if vehicle.capacity - total_weight < min_extra_capacity:
                min_extra_capacity = vehicle.capacity - total_weight
                best_vehicle = vehicle
            continue
        if can_stack_in_height(cargo_list, v_height):
            if vehicle.capacity - total_weight < min_extra_capacity:
                min_extra_capacity = vehicle.capacity - total_weight
                best_vehicle = vehicle

    if best_vehicle:
        return jsonify({
            "message": "Suitable vehicle found",
            "vehicle": best_vehicle.to_dict(),
            "total_weight": total_weight,
            "required_dimensions": {
                "length": max_l,
                "width": max_w,
                "height_strategy": "stacked" if best_vehicle.height < max_h_single else "no_stacking",
            },
            "note": "Грузы можно штабелировать по высоте" if best_vehicle.height < max_h_single else "Штабелирование не требуется",
        })

    # Если не нашли с указанным типом тента, ищем любую подходящую
    all_suitable_vehicles = Vehicle.query.filter(
        Vehicle.status == "free",
        Vehicle.capacity >= total_weight,
        Vehicle.length >= max_l,
        Vehicle.width >= max_w,
        Vehicle.status != "in_repair"
    ).all()

    print(f"[DEBUG] Now searching all {len(all_suitable_vehicles)} vehicles regardless of tent type")

    for vehicle in all_suitable_vehicles:
        v_height = vehicle.height
        if v_height >= max_h_single:
            if vehicle.capacity - total_weight < min_extra_capacity:
                min_extra_capacity = vehicle.capacity - total_weight
                best_vehicle = vehicle
            continue
        if can_stack_in_height(cargo_list, v_height):
            if vehicle.capacity - total_weight < min_extra_capacity:
                min_extra_capacity = vehicle.capacity - total_weight
                best_vehicle = vehicle

    if best_vehicle:
        return jsonify({
            "message": "Suitable vehicle found (different tent type)",
            "vehicle": best_vehicle.to_dict(),
            "warning": f"Не найдена машина с типом тента '{required_tent_type}'. Предлагается машина с типом тента '{best_vehicle.tent_type}'",
            "total_weight": total_weight,
            "required_dimensions": {
                "length": max_l,
                "width": max_w,
                "height_strategy": "stacked" if best_vehicle.height < max_h_single else "no_stacking",
            },
        })

    return jsonify({
        "message": "No suitable vehicle found",
        "required": {
            "weight": total_weight,
            "length": max_l,
            "width": max_w,
            "height_single": max_h_single,
            "height_stacked_estimate": sum(c["height"] * c["quantity"] for c in cargo_list),
            "tent_type": required_tent_type,
        },
    }), 404

@app.route("/auto_distribute_smart", methods=["POST"])
@login_required
@role_required("admin")
def auto_distribute_smart():
    """
    Умное автоматическое распределение с учетом:
    - Приоритета заявок
    - Времени отправления
    - Группировки по направлениям
    - Оптимизации загрузки
    """
    try:
        # Получаем все новые заявки
        new_orders = Order.query.filter_by(status="new").order_by(
            # Сначала по приоритету (high > normal > low)
            Order.priority.desc(),
            # Затем по времени отправления (раньше -> позже)
            Order.preferred_departure_date.asc()  # ВМЕСТО preferred_departure_time
        ).all()

        # Получаем свободные машины
        free_vehicles = Vehicle.query.filter_by(status="free").all()

        if not free_vehicles:
            return jsonify({"error": "Нет свободных машин"}), 400

        if not new_orders:
            return jsonify({"error": "Нет новых заявок"}), 400

        # Группируем заявки по направлениям (по первому пункту назначения)
        orders_by_direction = {}
        for order in new_orders:
            if order.cargos:
                # Берем первый пункт назначения как ключ направления
                first_destination = order.cargos[0].destination
                if first_destination not in orders_by_direction:
                    orders_by_direction[first_destination] = []
                orders_by_direction[first_destination].append(order)

        # Распределение
        assignments = []
        used_vehicles = []

        for direction, orders in orders_by_direction.items():
            # Группируем грузы по типу тента для этого направления
            cargos_by_tent = {}
            for order in orders:
                for cargo in order.cargos:
                    tent_type = cargo.tent_type
                    if tent_type not in cargos_by_tent:
                        cargos_by_tent[tent_type] = []
                    cargos_by_tent[tent_type].append({
                        "cargo": cargo,
                        "order_id": order.id
                    })

            # Распределяем для каждого типа тента
            for tent_type, cargo_items in cargos_by_tent.items():
                # Находим машины с нужным типом тента
                available_vehicles = [v for v in free_vehicles
                                    if v.tent_type == tent_type and v.id not in used_vehicles]

                if not available_vehicles:
                    continue

                # Сортируем грузы по объему (большие сначала)
                cargo_items.sort(key=lambda x: x["cargo"].length * x["cargo"].width * x["cargo"].height,
                               reverse=True)

                # Алгоритм "First Fit Decreasing" для упаковки
                for vehicle in available_vehicles:
                    vehicle_cargos = []
                    remaining_weight = vehicle.capacity
                    remaining_volume = vehicle.length * vehicle.width * vehicle.height

                    for item in cargo_items[:]:  # Копия для итерации
                        cargo = item["cargo"]
                        cargo_weight = cargo.weight * cargo.quantity
                        cargo_volume = cargo.length * cargo.width * cargo.height * cargo.quantity

                        if (cargo_weight <= remaining_weight and
                            cargo_volume <= remaining_volume and
                            cargo.length <= vehicle.length and
                            cargo.width <= vehicle.width and
                            cargo.height <= vehicle.height):

                            vehicle_cargos.append(item)
                            remaining_weight -= cargo_weight
                            remaining_volume -= cargo_volume
                            cargo_items.remove(item)  # Удаляем из списка доступных

                    if vehicle_cargos:
                        # Создаем объединенную заявку
                        new_order = Order(
                            status="assigned",
                            vehicle_id=vehicle.id,
                            applicant="Автоматическое объединение",
                            department="Система",
                            user_id=current_user.id,
                            note=f"Объединены заявки: {', '.join(set(str(item['order_id']) for item in vehicle_cargos))}. Направление: {direction}"
                        )

                        db.session.add(new_order)
                        db.session.flush()

                        # Добавляем грузы
                        for item in vehicle_cargos:
                            new_order.cargos.append(item["cargo"])

                        # Обновляем статусы исходных заявок
                        for order_id in set(item['order_id'] for item in vehicle_cargos):
                            order = Order.query.get(order_id)
                            order.status = "assigned"
                            order.note = f"Объединена в заявку #{new_order.id}"

                        # Обновляем машину
                        vehicle.status = "busy"
                        used_vehicles.append(vehicle.id)

                        assignments.append({
                            "vehicle": vehicle.garage_number,
                            "direction": direction,
                            "cargos_count": len(vehicle_cargos),
                            "new_order_id": new_order.id
                        })

        db.session.commit()

        return jsonify({
            "message": "Умное распределение завершено",
            "assignments": assignments,
            "statistics": {
                "orders_processed": len(new_orders),
                "vehicles_used": len(used_vehicles),
                "directions_covered": len(orders_by_direction)
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Ошибка распределения: {str(e)}"}), 500


def get_status_text(status):
    if status == "new":
        return "Новая"
    elif status == "assigned":
        return "Назначена"
    elif status == "completed":
        return "Завершена"
    return status

@app.route("/export_orders")
def export_orders():
    orders = Order.query.all()
    wb: Workbook = Workbook()
    ws: Worksheet = wb.active or wb.create_sheet("Рейсы")
    ws.title = "Рейсы"
    ws.append(["ID", "Создано", "Желаемая дата", "Статус", "Водитель", "Гос. номер", "Грузов", "Общий вес"])
    for o in orders:
        created = o.created_at.strftime("%d.%m.%Y %H:%M") if o.created_at else "-"

        # Форматируем желаемую ДАТУ (ВМЕСТО времени)
        preferred_date = "-"
        if o.preferred_departure_date:
            preferred_date = o.preferred_departure_date.strftime("%d.%m.%Y")  # Формат даты

        status = get_status_text(o.status)
        driver = o.vehicle.driver if o.vehicle else "-"
        gos_number = o.vehicle.gos_number if o.vehicle else "-"
        cargo_count = len(o.cargos)
        total_weight = sum(c.weight * c.quantity for c in o.cargos) if o.cargos else 0
        ws.append([o.id, created, preferred_date, status, driver, gos_number, cargo_count, total_weight])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="reyisy.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route("/route_sheet/<int:order_id>", methods=["GET"])
def print_route_sheet(order_id):
    """Генерация редактируемого маршрутного листа"""
    order = Order.query.get_or_404(order_id)

    if not order.vehicle:
        return jsonify({"error": "Нет назначенной машины"}), 400

    # Формируем HTML для маршрутного листа
    created_date = order.created_at.strftime("%d.%m.%Y") if order.created_at else datetime.now().strftime("%d.%m.%Y")
    today_date = datetime.now().strftime("%d.%m.%Y")

    # Таблица грузов - каждый груз отдельной строкой
    cargo_table = ""
    cargo_counter = 1

    for cargo in order.cargos:
        for i in range(cargo.quantity):  # Каждую единицу груза отдельной строкой
            cargo_table += f"""
            <tr>
                <td class="col-no">{cargo_counter}</td>
                <td class="col-request" contenteditable="true" class="editable">{cargo.name} → {cargo.destination}</td>
                <td class="col-address" contenteditable="true" class="editable">{cargo.destination}</td>
                <td class="col-time"><input type="time" class="editable" value="09:00"></td>
                <td class="col-work"><input type="text" class="editable" value="1 ч"></td>
                <td class="col-weight">{cargo.weight} кг</td>
                <td class="col-phone"><input type="text" class="editable" value="{order.phone_number or ''}"></td>
                <td class="col-comment" contenteditable="true" class="editable"></td>
                <td class="col-note" contenteditable="true" class="editable"></td>
            </tr>
            """
            cargo_counter += 1

    route_sheet_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Маршрутный лист №{order.id}</title>
    <style>
        /* Базовые стили для экрана */
        * {{
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Times New Roman', serif;
            margin: 0;
            padding: 20px 40px;
            font-size: 15px;
            line-height: 1.5;
            background: white;
        }}

        .print-container {{
            width: 100%;
            max-width: 100%;
        }}

        .company-header {{
            text-align: center;
            font-weight: bold;
            margin-bottom: 20px;
            font-size: 20px;
        }}

        .driver-info {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 25px;
            font-size: 16px;
            padding: 0 10px;
        }}

        .driver-info div {{
            width: 48%;
        }}

        .underline {{
            border-bottom: 1px solid #000;
            display: inline-block;
            min-width: 250px;
            margin-left: 15px;
        }}

        .document-title {{
            text-align: center;
            font-weight: bold;
            margin: 25px 0;
            font-size: 18px;
            padding: 0 10px;
        }}

        /* Таблица для экрана */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 25px 0;
            font-size: 14px;
            table-layout: fixed;
        }}

        th, td {{
            border: 1px solid #000;
            padding: 10px 8px;
            text-align: center;
            vertical-align: middle;
            overflow: hidden;
            text-overflow: ellipsis;
            min-height: 40px;
        }}

        th {{
            font-weight: bold;
            background-color: #f0f0f0;
            font-size: 15px;
            padding: 12px 8px;
        }}

        /* Увеличенные ширины колонок в процентах */
        .col-no {{ width: 4%; }}
        .col-request {{ width: 20%; text-align: left; }}
        .col-address {{ width: 17%; text-align: left; }}
        .col-time {{ width: 12%; }}
        .col-work {{ width: 10%; }}
        .col-weight {{ width: 8%; }}
        .col-phone {{ width: 12%; }}
        .col-comment {{ width: 16%; text-align: left; }}
        .col-note {{ width: 17%; text-align: left; }}

        .editable {{
            outline: none;
            width: 100%;
            display: block;
            min-height: 30px;
            padding: 4px;
        }}

        .editable:focus {{
            background-color: #ffffcc;
            border: 1px dashed #666 !important;
        }}

        .signatures {{
            margin-top: 50px;
            padding: 0 10px;
        }}

        .signature-line {{
            display: flex;
            justify-content: space-between;
            margin-top: 40px;
        }}

        .signature-block {{
            width: 45%;
        }}

        .signature-name {{
            margin-bottom: 15px;
            font-weight: bold;
            font-size: 16px;
        }}

        .signature-space {{
            border-bottom: 1px solid #000;
            height: 50px;
            margin-top: 8px;
        }}

        .signature-label {{
            font-size: 13px;
            color: #666;
            margin-top: 8px;
            text-align: center;
        }}

        .controls {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: white;
            padding: 15px;
            border: 2px solid #ccc;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
        }}

        .btn {{
            padding: 10px 20px;
            margin: 5px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
        }}

        .btn-print {{ background: #4caf50; color: white; }}
        .btn-edit {{ background: #2196f3; color: white; }}
        .btn-save {{ background: #ff9800; color: white; }}
        .btn-close {{ background: #f44336; color: white; }}

        input[type="time"], input[type="text"] {{
            font-family: 'Times New Roman', serif;
            font-size: 14px;
            width: 100%;
            border: none;
            background: transparent;
            text-align: center;
            padding: 6px;
            height: 35px;
        }}

        input[type="time"]:focus, input[type="text"]:focus {{
            background: #ffffcc;
            border: 1px dashed #666 !important;
            outline: none;
        }}

        /* Стили ТОЛЬКО для печати */
        @media print {{
            /* Скрываем все ненужное */
            .no-print {{
                display: none !important;
            }}

            /* Отступы: сверху 3см, слева/справа 1.75см */
            @page {{
                size: landscape;
                margin: 3cm 1.75cm;
            }}

            /* Стили для тела документа при печати */
            body {{
                margin: 0;
                padding: 0;
                width: 100%;
                font-family: 'Times New Roman', serif !important;
                font-size: 12pt !important;  /* Увеличенный шрифт */
                line-height: 1.3 !important;
                background: white !important;
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
            }}

            .print-container {{
                width: 100% !important;
                max-width: 100% !important;
                padding: 0 !important;
                margin: 0 !important;
            }}

            /* Увеличенные размеры для печати */
            .company-header {{
                font-size: 16pt !important;
                margin-bottom: 12pt !important;
                text-align: center !important;
            }}

            .driver-info {{
                font-size: 13pt !important;
                margin-bottom: 16pt !important;
                padding: 0 15pt !important;
            }}

            .underline {{
                min-width: 180pt !important;
            }}

            .document-title {{
                font-size: 14pt !important;
                margin: 16pt 0 !important;
                padding: 0 15pt !important;
            }}

            /* Стили для таблицы при печати */
            table {{
                width: 100% !important;
                max-width: 100% !important;
                table-layout: fixed !important;
                border-collapse: collapse !important;
                border-spacing: 0 !important;
                margin: 15pt 0 !important;
                font-size: 11pt !important;  /* Увеличенный шрифт таблицы */
                page-break-inside: auto !important;
            }}

            th, td {{
                border: 1px solid black !important;
                padding: 8pt 6pt !important;  /* Увеличенные отступы */
                font-size: 11pt !important;
                line-height: 1.3 !important;
                overflow: visible !important;
                text-overflow: clip !important;
                white-space: normal !important;
                word-wrap: break-word !important;
                height: auto !important;
                min-height: 25pt !important;  /* Увеличенная высота */
                vertical-align: middle !important;
            }}

            th {{
                font-size: 12pt !important;
                padding: 10pt 6pt !important;
            }}

            /* Принудительный перенос длинных слов */
            th, td {{
                word-break: break-word !important;
                overflow-wrap: break-word !important;
            }}

            /* Увеличенные ширины колонок для печати (в процентах) */
            .col-no {{ width: 4% !important; }}
            .col-request {{ width: 22% !important; }}
            .col-address {{ width: 18% !important; }}
            .col-time {{ width: 13% !important; }}
            .col-work {{ width: 11% !important; }}
            .col-weight {{ width: 9% !important; }}
            .col-phone {{ width: 13% !important; }}
            .col-comment {{ width: 17% !important; }}
            .col-note {{ width: 18% !important; }}

            /* Скрываем элементы редактирования при печати */
            .editable {{
                background: transparent !important;
                border: none !important;
                min-height: 25pt !important;
            }}

            input[type="time"], input[type="text"] {{
                border: none !important;
                background: transparent !important;
                font-size: 11pt !important;
                -webkit-appearance: none !important;
                appearance: none !important;
                padding: 4pt !important;
            }}

            /* Скрываем индикатор выбора времени */
            input[type="time"]::-webkit-calendar-picker-indicator {{
                display: none !important;
            }}

            input[type="time"]::-webkit-inner-spin-button {{
                display: none !important;
            }}

            /* Подписи */
            .signatures {{
                margin-top: 25pt !important;
                padding: 0 15pt !important;
            }}

            .signature-line {{
                margin-top: 20pt !important;
            }}

            .signature-space {{
                height: 25pt !important;
            }}

            .signature-name {{
                font-size: 13pt !important;
                margin-bottom: 10pt !important;
            }}

            /* Гарантируем черно-белую печать */
            * {{
                color: black !important;
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
            }}

            /* Разрешаем разрыв страницы после таблицы */
            .signatures {{
                page-break-before: avoid !important;
            }}

            /* Убираем любые тени и скругления */
            .btn, .controls, .no-print {{
                display: none !important;
            }}
        }}

        /* Дополнительные стили для экрана */
        @media screen {{
            body {{
                background-color: #f5f5f5;
            }}

            .print-container {{
                background: white;
                padding: 30px;
                margin: 20px auto;
                max-width: 1800px;  /* Увеличенная максимальная ширина */
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }}
        }}
    </style>
</head>
<body>
    <div class="print-container">
        <div class="driver-info">

            <div>
                Водитель: <span class="text-align:left">{order.vehicle.driver}</span>
                Машина: <span class="text-align:left">{order.vehicle.brand} ({order.vehicle.gos_number})</span>
            </div>

        </div>

        <div>
            Маршрутный лист от {today_date} к путевому листу № _____
            <span class="editable underline" contenteditable="false" style="min-width: 60px; display: inline-block; text-align: left;"></span>
        </div>

        <table>
            <thead>
                <tr>
                    <th class="col-no">№</th>
                    <th class="col-request">Заявка</th>
                    <th class="col-address">Адрес</th>
                    <th class="col-time">Планируемое прибытие</th>
                    <th class="col-work">Время работы</th>
                    <th class="col-weight">Вес кг.</th>
                    <th class="col-phone">Телефон</th>
                    <th class="col-comment">Комментарий</th>
                    <th class="col-note">Примечание</th>
                </tr>
            </thead>
            <tbody>
                {cargo_table}
            </tbody>
        </table>

        <div class="signatures">
            <div class="signature-line">
                <div class="signature-block">
                    <div class="signature-name">Логистик выдал:</div>
                    <div class="signature-name">Водитель сдал:</div>
                </div>
            </div>
        </div>
    </div>

    <div class="controls no-print">
        <button class="btn btn-edit" onclick="enableEditing()">✏️ Редактировать</button>
        <button class="btn btn-save" onclick="saveChanges()" style="display:none;">💾 Сохранить</button>
        <button class="btn btn-print" onclick="printOptimized()">🖨️ Печать</button>
        <button class="btn btn-close" onclick="window.close()">✕ Закрыть</button>
    </div>

    <script>
        let isEditing = false;
        let savedData = null;

        // Функция для подготовки к печати
        function prepareForPrint() {{
            // Сохраняем текущие значения полей ввода
            document.querySelectorAll('input').forEach(input => {{
                if (input.type === 'time' || input.type === 'text') {{
                    // Создаем текстовый span с значением
                    const span = document.createElement('span');
                    span.textContent = input.value;
                    span.style.display = 'inline-block';
                    span.style.width = '100%';
                    span.style.textAlign = 'center';

                    // Заменяем input на span
                    input.parentNode.insertBefore(span, input);
                    input.style.display = 'none';
                }}
            }});

            // Убираем все атрибуты contenteditable
            document.querySelectorAll('[contenteditable="true"]').forEach(el => {{
                el.setAttribute('contenteditable', 'false');
            }});

            // Принудительный reflow
            document.body.offsetHeight;

            return true;
        }}

        // Функция для восстановления после печати
        function restoreAfterPrint() {{
            // Восстанавливаем поля ввода
            document.querySelectorAll('td').forEach(td => {{
                const span = td.querySelector('span');
                const hiddenInput = td.querySelector('input[style*="display: none"]');

                if (span && hiddenInput) {{
                    // Возвращаем значение в input
                    hiddenInput.value = span.textContent;
                    hiddenInput.style.display = '';
                    span.remove();
                }}
            }});

            // Восстанавливаем режим редактирования если нужно
            if (isEditing) {{
                enableEditing();
            }}
        }}

        // Оптимизированная печать
        function printOptimized() {{
            // Сохраняем изменения если в режиме редактирования
            if (isEditing) {{
                saveChanges();
            }}

            // Подготавливаем документ к печати
            prepareForPrint();

            // Запускаем печать с небольшой задержкой
            setTimeout(() => {{
                window.print();

                // Восстанавливаем после печати
                setTimeout(restoreAfterPrint, 500);
            }}, 200);
        }}

        function enableEditing() {{
            isEditing = true;

            document.querySelectorAll('.editable').forEach(el => {{
                el.setAttribute('contenteditable', 'true');
                if (el.style) el.style.backgroundColor = '#ffffcc';
            }});

            document.querySelectorAll('input').forEach(input => {{
                input.removeAttribute('readonly');
                if (input.style) {{
                    input.style.backgroundColor = '#ffffcc';
                    input.style.border = '1px dashed #999';
                }}
            }});

            document.querySelector('.btn-edit').style.display = 'none';
            document.querySelector('.btn-save').style.display = 'inline-block';
        }}

        function disableEditing() {{
            isEditing = false;

            document.querySelectorAll('.editable').forEach(el => {{
                el.setAttribute('contenteditable', 'false');
                if (el.style) el.style.backgroundColor = '';
            }});

            document.querySelectorAll('input').forEach(input => {{
                input.setAttribute('readonly', true);
                if (input.style) {{
                    input.style.backgroundColor = 'transparent';
                    input.style.border = 'none';
                }}
            }});

            document.querySelector('.btn-edit').style.display = 'inline-block';
            document.querySelector('.btn-save').style.display = 'none';
        }}

        function saveChanges() {{
            const changes = {{
                driver: document.querySelector('.driver-info .editable:first-child')?.textContent || '',
                vehicle: document.querySelector('.driver-info .editable:last-child')?.textContent || '',
                waybill_number: document.querySelector('.document-title .editable')?.textContent || '',
                cargo_items: []
            }};

            document.querySelectorAll('tbody tr').forEach((row) => {{
                const cells = row.querySelectorAll('td');
                if (cells.length >= 9) {{
                    changes.cargo_items.push({{
                        request: cells[1]?.textContent || '',
                        address: cells[2]?.textContent || '',
                        arrival_time: cells[3]?.querySelector('input')?.value || '',
                        work_time: cells[4]?.querySelector('input')?.value || '',
                        phone: cells[6]?.querySelector('input')?.value || '',
                        comment: cells[7]?.textContent || '',
                        note: cells[8]?.textContent || ''
                    }});
                }}
            }});

            savedData = changes;
            localStorage.setItem('route_sheet_{order.id}', JSON.stringify(changes));

            disableEditing();
            showNotification('Изменения сохранены');
        }}

        function showNotification(message) {{
            const notification = document.createElement('div');
            notification.textContent = message;
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #4caf50;
                color: white;
                padding: 15px 20px;
                border-radius: 4px;
                z-index: 1001;
                animation: slideIn 0.3s ease-out;
                font-weight: bold;
                box-shadow: 0 3px 10px rgba(0,0,0,0.2);
            `;

            document.body.appendChild(notification);

            setTimeout(() => {{
                notification.style.animation = 'slideOut 0.3s ease-out';
                setTimeout(() => notification.remove(), 300);
            }}, 2000);
        }}

        // Добавляем стили для анимации
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {{
                from {{ transform: translateX(100%); opacity: 0; }}
                to {{ transform: translateX(0); opacity: 1; }}
            }}
            @keyframes slideOut {{
                from {{ transform: translateX(0); opacity: 1; }}
                to {{ transform: translateX(100%); opacity: 0; }}
            }}
        `;
        document.head.appendChild(style);

        // Загружаем сохраненные данные
        window.onload = function() {{
            const saved = localStorage.getItem('route_sheet_{order.id}');
            if (saved) {{
                savedData = JSON.parse(saved);

                const driverSpan = document.querySelector('.driver-info .editable:first-child');
                const vehicleSpan = document.querySelector('.driver-info .editable:last-child');
                const waybillSpan = document.querySelector('.document-title .editable');

                if (driverSpan && savedData.driver) driverSpan.textContent = savedData.driver;
                if (vehicleSpan && savedData.vehicle) vehicleSpan.textContent = savedData.vehicle;
                if (waybillSpan && savedData.waybill_number) waybillSpan.textContent = savedData.waybill_number;

                if (savedData.cargo_items && savedData.cargo_items.length > 0) {{
                    document.querySelectorAll('tbody tr').forEach((row, index) => {{
                        if (savedData.cargo_items[index]) {{
                            const cells = row.querySelectorAll('td');
                            const item = savedData.cargo_items[index];

                            if (cells[1]) cells[1].textContent = item.request || '';
                            if (cells[2]) cells[2].textContent = item.address || '';

                            const arrivalInput = cells[3]?.querySelector('input');
                            const workInput = cells[4]?.querySelector('input');
                            const phoneInput = cells[6]?.querySelector('input');

                            if (arrivalInput) arrivalInput.value = item.arrival_time || '';
                            if (workInput) workInput.value = item.work_time || '';
                            if (phoneInput) phoneInput.value = item.phone || '';
                            if (cells[7]) cells[7].textContent = item.comment || '';
                            if (cells[8]) cells[8].textContent = item.note || '';
                        }}
                    }});
                }}
            }}

            // Автоматически подгоняем размер шрифта для таблицы
            const table = document.querySelector('table');
            if (table) {{
                const rowCount = table.querySelectorAll('tbody tr').length;
                if (rowCount > 12) {{
                    table.style.fontSize = '12px';
                }}
            }}
        }};

        // Горячие клавиши
        document.addEventListener('keydown', function(event) {{
            if ((event.ctrlKey || event.metaKey) && event.key === 's') {{
                event.preventDefault();
                if (isEditing) saveChanges();
            }}

            if ((event.ctrlKey || event.metaKey) && event.key === 'p') {{
                event.preventDefault();
                printOptimized();
            }}

            if (event.key === 'Escape' && isEditing) {{
                disableEditing();
            }}
        }});
    </script>
</body>
</html>"""

    return route_sheet_html


@app.route("/orders/<int:id>", methods=["DELETE"])
@login_required
def delete_order(id):

    if not current_user.is_authenticated or current_user.role != "admin":
        return jsonify({"error": "Только администратор"}), 403


    order = Order.query.get_or_404(id)

    # Нельзя удалять уже назначенные или завершённые заявки
    if order.status != "new":
        return jsonify({"error": "Можно удалять только новые заявки"}), 400

    # Удаляем связанные грузы (они только в этой заявке)
    for cargo in order.cargos:
        db.session.delete(cargo)

    db.session.delete(order)
    db.session.commit()
    return jsonify({"message": "Заявка удалена"}), 200



@app.route("/route_sheet/<int:order_id>/save", methods=["POST"])
@login_required
def save_route_sheet(order_id):
    """Сохранение отредактированного маршрутного листа"""
    order = Order.query.get_or_404(order_id)
    data = request.get_json()

    # Сохраняем изменения в отдельной таблице или в поле note
    if not order.note:
        order.note = ""

    route_sheet_data = {
        "departure": data.get("departure"),
        "destination": data.get("destination"),
        "distance": data.get("distance"),
        "departure_time": data.get("departure_time"),
        "special_notes": data.get("special_notes"),
        "cargo_notes": data.get("cargo_notes", []),
        "saved_by": current_user.username,
        "saved_at": datetime.now(timezone.utc).isoformat()
    }

    # Добавляем к существующим примечаниям
    if "Маршрутный лист" not in order.note:
        order.note += f"\n\n=== Маршрутный лист ===\n"

    order.note += f"Отредактирован: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
    order.note += f"Маршрут: {data.get('departure')} -> {data.get('destination')}\n"
    order.note += f"Пробег: {data.get('distance')}\n"

    db.session.commit()

    return jsonify({"message": "Маршрутный лист сохранен", "order_id": order.id})


@app.route("/orders/<int:id>/unassign", methods=["POST"])
@login_required
def unassign_vehicle(id):
    """Снять назначенную машину с заявки"""
    if not current_user.is_authenticated or current_user.role != "admin":
        return jsonify({"error": "Только администратор"}), 403

    order = Order.query.get_or_404(id)

    if order.status != "assigned":
        return jsonify({"error": "Можно снимать машину только с назначенных заявок"}), 400

    if not order.vehicle_id:
        return jsonify({"error": "У заявки нет назначенной машины"}), 400

    # Находим активный рейс для этой заявки
    trip = Trip.query.filter_by(order_id=order.id, status="in_progress").first()

    # Освобождаем машину
    vehicle = Vehicle.query.get(order.vehicle_id)
    if vehicle:
        vehicle.status = "free"

    # Отменяем рейс (меняем статус на cancelled)
    if trip:
        trip.status = "cancelled"
        trip.completed_at = datetime.now(timezone.utc)
        trip.notes = f"Машина снята администратором {current_user.username}"

    # Возвращаем заявку в статус "new"
    order.status = "new"
    order.vehicle_id = None

    db.session.commit()

    return jsonify({
        "message": "Машина снята с заявки",
        "order": order.to_dict(),
        "vehicle_freed": vehicle.to_dict() if vehicle else None
    }), 200




@app.route("/orders/<int:id>", methods=["PUT"])
@login_required
def update_order(id):
    if not current_user.is_authenticated or current_user.role != "admin":
        return jsonify({"error": "Только администратор"}), 403

    order = Order.query.get_or_404(id)
    if order.status != "new":
        return jsonify({"error": "Редактировать можно только новые заявки"}), 400

    data = request.get_json()

    order.applicant = data.get("applicant", order.applicant)
    order.department = data.get("department", order.department)
    order.phone_number = data.get("phone_number", order.phone_number)
    order.tent_type = data.get("tent_type", order.tent_type)
    order.note = data.get("note", order.note)

    # Обновляем желаемое время отправления
    if "preferred_departure_date" in data:
        if data["preferred_departure_date"]:
            try:
                date_str = data["preferred_departure_date"]
                order.preferred_departure_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except Exception as e:
                return jsonify({"error": f"Неверный формат даты: {str(e)}"}), 400
        else:
            order.preferred_departure_date = None

    db.session.commit()
    return jsonify(order.to_dict()), 200


@app.route("/orders/merge", methods=["POST"])
@login_required
@role_required("admin")
def merge_orders():
    """Объединение нескольких заявок в одну"""
    try:
        data = request.get_json()
        order_ids = data.get("order_ids", [])

        if len(order_ids) < 2:
            return jsonify({"error": "Выберите минимум 2 заявки"}), 400

        # Проверяем заявки
        orders = Order.query.filter(Order.id.in_(order_ids)).all()

        # Проверяем статусы (можно объединять только новые заявки)
        for order in orders:
            if order.status != "new":
                return jsonify({"error": f"Заявка #{order.id} уже назначена"}), 400

        # Проверяем совместимость типов тента грузов
        all_cargos = []
        for order in orders:
            all_cargos.extend(order.cargos)

        # Создаем новую объединенную заявку
        merged_order = Order(
            status="new",
            applicant="Объединенная заявка",
            department="Система",
            user_id=current_user.id,
            note=f"Объединены заявки: {', '.join(map(str, order_ids))}"
        )

        db.session.add(merged_order)
        db.session.flush()

        # Переносим грузы в новую заявку
        for cargo in all_cargos:
            # Отвязываем от старых заявок
            for order in orders:
                if cargo in order.cargos:
                    order.cargos.remove(cargo)

            # Добавляем в новую заявку
            merged_order.cargos.append(cargo)

        # Удаляем старые заявки
        for order in orders:
            db.session.delete(order)

        db.session.commit()

        return jsonify({
            "message": "Заявки успешно объединены",
            "new_order_id": merged_order.id,
            "merged_orders": order_ids,
            "cargos_count": len(all_cargos)
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Ошибка объединения: {str(e)}"}), 500


@app.route("/orders/<int:order_id>/split", methods=["POST"])
@login_required
@role_required("admin")
def split_order(order_id):
    """Разделение заявки на несколько по разным машинам"""
    try:
        order = Order.query.get_or_404(order_id)

        if order.status != "new":
            return jsonify({"error": "Можно разделять только новые заявки"}), 400

        if len(order.cargos) < 2:
            return jsonify({"error": "В заявке должен быть минимум 2 груза"}), 400

        data = request.get_json()
        split_groups = data.get("split_groups", [])

        if not split_groups:
            return jsonify({"error": "Укажите группы для разделения"}), 400

        # Проверяем, что все грузы распределены
        all_cargo_ids = {cargo.id for cargo in order.cargos}
        split_cargo_ids = {cargo_id for group in split_groups for cargo_id in group}

        if all_cargo_ids != split_cargo_ids:
            return jsonify({"error": "Не все грузы распределены по группам"}), 400

        # Создаем новые заявки для каждой группы
        new_orders = []
        for i, group in enumerate(split_groups):
            group_cargos = [cargo for cargo in order.cargos if cargo.id in group]

            if not group_cargos:
                continue

            new_order = Order(
                status="new",
                applicant=order.applicant,
                department=order.department,
                phone_number=order.phone_number,
                user_id=current_user.id,
                note=f"Часть от заявки #{order_id} (группа {i+1})"
            )

            db.session.add(new_order)
            db.session.flush()

            # Переносим грузы
            for cargo in group_cargos:
                order.cargos.remove(cargo)
                new_order.cargos.append(cargo)

            new_orders.append(new_order)

        # Удаляем исходную заявку
        db.session.delete(order)
        db.session.commit()

        return jsonify({
            "message": "Заявка разделена",
            "original_order_id": order_id,
            "new_orders": [o.id for o in new_orders],
            "groups_count": len(new_orders)
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Ошибка разделения: {str(e)}"}), 500

# Admin: CRUD for cargos in order (admin only, allowed only for 'new' orders)
@app.route("/orders/<int:order_id>/cargos", methods=["GET"])
@login_required
def list_order_cargos(order_id):
    if not current_user.is_authenticated or current_user.role != "admin":
        return jsonify({"error": "Только администратор"}), 403
    order = Order.query.get_or_404(order_id)
    return jsonify([c.to_dict() for c in order.cargos])

@app.route("/orders/<int:order_id>/cargos", methods=["POST"])
@login_required
def add_order_cargo(order_id):
    if not current_user.is_authenticated or current_user.role != "admin":
        return jsonify({"error": "Только администратор"}), 403
    order = Order.query.get_or_404(order_id)
    if order.status != "new":
        return jsonify({"error": "Можно изменять грузы только в новых заявках"}), 400
    data = request.get_json() or {}
    allowed = ["name", "weight", "length", "width", "height", "quantity", "departure", "destination"]
    payload = {k: data[k] for k in allowed if k in data}
    if len(payload) != len(allowed):
        return jsonify({"error": "Не все поля груза заполнены"}), 400
    cargo = Cargo(**payload)
    db.session.add(cargo)
    db.session.flush()
    order.cargos.append(cargo)
    db.session.commit()
    return jsonify(cargo.to_dict()), 201

@app.route("/orders/<int:order_id>/cargos/<int:cargo_id>", methods=["PUT", "PATCH"])
@login_required
def update_order_cargo(order_id, cargo_id):
    if not current_user.is_authenticated or current_user.role != "admin":
        return jsonify({"error": "Только администратор"}), 403
    order = Order.query.get_or_404(order_id)
    if order.status != "new":
        return jsonify({"error": "Можно изменять грузы только в новых заявках"}), 400
    cargo = Cargo.query.get_or_404(cargo_id)
    if cargo not in order.cargos:
        return jsonify({"error": "Груз не найден в этой заявке"}), 404
    data = request.get_json() or {}
    for field in ["name", "weight", "length", "width", "height", "quantity", "departure", "destination"]:
        if field in data:
            setattr(cargo, field, data[field])
    db.session.commit()
    return jsonify(cargo.to_dict()), 200

@app.route("/orders/<int:order_id>/cargos/<int:cargo_id>", methods=["DELETE"])
@login_required
def delete_order_cargo(order_id, cargo_id):
    if not current_user.is_authenticated or current_user.role != "admin":
        return jsonify({"error": "Только администратор"}), 403
    order = Order.query.get_or_404(order_id)
    if order.status != "new":
        return jsonify({"error": "Можно изменять грузы только в новых заявках"}), 400
    cargo = Cargo.query.get_or_404(cargo_id)
    if cargo not in order.cargos:
        return jsonify({"error": "Груз не найден в этой заявке"}), 404
    try:
        order.cargos.remove(cargo)
    except ValueError:
        pass
    db.session.delete(cargo)
    db.session.commit()
    return jsonify({"message": "Груз удалён"}), 200

# Маршруты для раздачи фронтенда с того же порта
_static_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))

@app.route("/", methods=["GET"])
def root_page():
    return send_file(os.path.join(_static_root, "login.html"))

@app.route("/index.html")
@login_required
def index_html():
    return send_file(os.path.join(_static_root, "index.html"))

@app.route("/login.html")
def login_html():
    return send_file(os.path.join(_static_root, "login.html"))


@app.route("/admin.html")
@login_required
@role_required("admin")
def admin_html():
    return send_file(os.path.join(_static_root, "admin.html"))

@app.route("/confirm.html")
def confirm_html():
    return send_file(os.path.join(_static_root, "confirm.html"))

@app.route("/script.js")
def script_js():
    return send_file(os.path.join(_static_root, "script.js"))

@app.route("/admin.js")
def admin_js():
    return send_file(os.path.join(_static_root, "admin.js"))

@app.route("/confirm.js")
def confirm_js():
    return send_file(os.path.join(_static_root, "confirm.js"))

@app.route("/style.css")
def style_css():
    return send_file(os.path.join(_static_root, "style.css"))

@app.route("/favicon.ico")
def favicon_ico():
    return send_file(os.path.join(_static_root, "favicon.ico"))

@app.after_request
def after_request(response):


    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'

    return response

def check_order_deadlines():
    """Проверяет заявки, у которых подходит срок отправления по ДАТЕ"""
    while True:
        with app.app_context():
            now = datetime.now(timezone.utc)
            # Проверяем заявки, у которых желаемая дата - сегодня или вчера (просроченные)
            urgent_orders = Order.query.filter(
                Order.status == 'new',
                Order.preferred_departure_date != None,
                Order.preferred_departure_date <= now.date()  # Сравниваем ДАТЫ
            ).all()

            for order in urgent_orders:
                # Можно отправить уведомление
                print(f"СРОЧНО: Заявка #{order.id} требует отправления {order.preferred_departure_date}")

        time.sleep(300)  # Проверять каждые 5 минут

@app.route("/trips", methods=["GET"])
@login_required
def get_trips():
    """Получение всех рейсов с фильтрацией"""
    # Фильтры из запроса
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    vehicle_id = request.args.get('vehicle_id')
    driver = request.args.get('driver')
    status = request.args.get('status')

    # Начинаем запрос
    query = Trip.query.join(Order, Trip.order_id == Order.id).join(Vehicle, Order.vehicle_id == Vehicle.id)

    if current_user.role != "admin":
        query = query.filter(Order.user_id == current_user.id)

    # Применяем фильтры
    if date_from:
        try:
            date_from_obj = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            query = query.filter(Trip.started_at >= date_from_obj)
        except:
            pass

    if date_to:
        try:
            date_to_obj = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            query = query.filter(Trip.started_at <= date_to_obj)
        except:
            pass

    if vehicle_id:
        query = query.filter(Vehicle.id == vehicle_id)

    if driver:
        query = query.filter(Vehicle.driver.ilike(f'%{driver}%'))

    if status:
        query = query.filter(Trip.status == status)

    # Сортировка по дате начала (новые сверху)
    trips = query.order_by(Trip.started_at.desc()).all()

    # Преобразуем в словари с подробной информацией
    trips_data = []
    for trip in trips:
        trip_dict = trip.to_dict()

        # Добавляем информацию о заказе
        order = Order.query.get(trip.order_id)
        if order:
            trip_dict['order'] = order.to_dict()

            # Добавляем информацию о машине
            if order.vehicle:
                trip_dict['vehicle'] = order.vehicle.to_dict()

            # Добавляем статистику по грузам
            if order.cargos:
                total_weight = sum(c.weight * c.quantity for c in order.cargos)
                total_volume = sum(c.length * c.width * c.height * c.quantity for c in order.cargos)
                cargo_count = len(order.cargos)

                trip_dict['cargo_stats'] = {
                    'total_weight': total_weight,
                    'total_volume': total_volume,
                    'cargo_count': cargo_count,
                    'routes': list(set(f"{c.departure} → {c.destination}" for c in order.cargos))
                }

        trips_data.append(trip_dict)

    return jsonify(trips_data)


@app.route("/trips/<int:trip_id>/complete", methods=["POST"])
@login_required
@role_required("admin")
def complete_trip(trip_id):
    """Завершение рейса"""
    trip = Trip.query.get_or_404(trip_id)

    if trip.status != "in_progress":
        return jsonify({"error": "Рейс уже завершен или отменен"}), 400

    trip.status = "completed"
    trip.completed_at = datetime.now(timezone.utc)

    # Обновляем статус заявки
    order = Order.query.get(trip.order_id)
    if order:
        order.status = "completed"

        # Освобождаем машину
        if order.vehicle:
            order.vehicle.status = "free"

    db.session.commit()

    return jsonify({
        "message": "Рейс завершен",
        "trip": trip.to_dict()
    })

@app.route("/trips/<int:trip_id>", methods=["GET"])
@login_required
def get_trip_by_id(trip_id):
    """Получение данных конкретного рейса по ID"""
    trip = Trip.query.get_or_404(trip_id)

    # Проверяем права доступа
    if current_user.role != "admin":
        # Пользователь может видеть только свои рейсы
        order = Order.query.get(trip.order_id)
        if order and order.user_id != current_user.id:
            return jsonify({"error": "Доступ запрещён"}), 403

    trip_dict = trip.to_dict()

    # Добавляем информацию о заказе
    order = Order.query.get(trip.order_id)
    if order:
        trip_dict['order'] = order.to_dict()

        # Добавляем информацию о машине
        if order.vehicle:
            trip_dict['vehicle'] = order.vehicle.to_dict()

        # Добавляем статистику по грузам
        if order.cargos:
            total_weight = sum(c.weight * c.quantity for c in order.cargos)
            total_volume = sum(c.length * c.width * c.height * c.quantity for c in order.cargos)
            cargo_count = len(order.cargos)

            trip_dict['cargo_stats'] = {
                'total_weight': total_weight,
                'total_volume': total_volume,
                'cargo_count': cargo_count,
                'routes': list(set(f"{c.departure} → {c.destination}" for c in order.cargos))
            }

    return jsonify(trip_dict)


@app.route("/trips/stats", methods=["GET"])
@login_required
def get_trips_stats():
    """Статистика по рейсам"""
    # За последние 30 дней
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

    # Общая статистика
    total_trips = Trip.query.count()
    completed_trips = Trip.query.filter_by(status="completed").count()
    in_progress_trips = Trip.query.filter_by(status="in_progress").count()

    # Статистика за последние 30 дней
    recent_trips = Trip.query.filter(Trip.started_at >= thirty_days_ago).count()
    recent_completed = Trip.query.filter(
        Trip.status == "completed",
        Trip.started_at >= thirty_days_ago
    ).count()

    # Статистика по машинам
    vehicle_stats = db.session.query(
        Vehicle.brand,
        Vehicle.driver,
        db.func.count(Trip.id).label('trip_count'),
        db.func.sum(
            db.func.coalesce(
                db.func.cast((
                    select([db.func.sum(Cargo.weight * Cargo.quantity)])
                    .where(Cargo.id.in_(
                        select([order_cargo.c.cargo_id])
                        .where(order_cargo.c.order_id == Trip.order_id)
                    ))
                    .as_scalar()
                ), db.Float), 0)
        ).label('total_weight')
    ).join(Order, Order.id == Trip.order_id).join(
        Vehicle, Vehicle.id == Order.vehicle_id
    ).filter(Trip.status == "completed").group_by(
        Vehicle.id, Vehicle.brand, Vehicle.driver
    ).order_by(db.desc('trip_count')).limit(10).all()

    return jsonify({
        "total_trips": total_trips,
        "completed_trips": completed_trips,
        "in_progress_trips": in_progress_trips,
        "recent_30_days": {
            "total": recent_trips,
            "completed": recent_completed,
            "completion_rate": (recent_completed / recent_trips * 100) if recent_trips > 0 else 0
        },
        "top_vehicles": [
            {
                "brand": stat.brand,
                "driver": stat.driver,
                "trip_count": stat.trip_count,
                "total_weight": float(stat.total_weight or 0)
            }
            for stat in vehicle_stats
        ]
    })



if __name__ == "__main__":
    with app.app_context():
        if not User.query.first():

            user = User(username="user", password=generate_password_hash("sazwork205"), role="user")

            admin = User(username="admin", password=generate_password_hash("sazadmin2025"), role="admin")

            db.session.add(user)

            db.session.add(admin)

            db.session.commit()

        db.create_all()
        thread = Thread(target=check_order_deadlines, daemon=True)
        thread.start()
    app.run(debug=True, port=5000)
