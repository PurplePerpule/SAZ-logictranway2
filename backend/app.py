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
from openpyxl.utils import get_column_letter
from urllib.parse import quote
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import base64
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from xhtml2pdf import pisa

import os
from pathlib import Path

app = Flask(__name__)
CORS(app)


app.config["SECRET_KEY"] = "c639183901c409352be3d01c521c7694"

login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


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
    length = db.Column(db.Float, nullable=False)
    width = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    departure = db.Column(db.String(200), nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    height = db.Column(db.Float, nullable=False)
    tent_type = db.Column(db.String(20), nullable=False, default="closed")

    # Добавьте это отношение
    orders = relationship("Order", secondary=order_cargo, back_populates="cargos")

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
            "tent_type": self.tent_type,
        }

class DraftCargo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    length = db.Column(db.Float, nullable=False)
    width = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    departure = db.Column(db.String(200), nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tent_type = db.Column(db.String(20), nullable=False, default="closed")

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
            "quantity": self.quantity,
            "departure": self.departure,
            "destination": self.destination,
            "tent_type": self.tent_type,
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
    preferred_departure_time = db.Column(db.DateTime, nullable=True)
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
            "preferred_departure_time": self.preferred_departure_time.isoformat() if self.preferred_departure_time else None,
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
        # Админ видит все заявки, сортируем по статусу (новые сверху) и дате создания
        orders = Order.query.order_by(
            Order.status.asc(),  # 'new' будет первым в алфавитном порядке
            Order.created_at.desc()  # Новые заявки сверху
        ).all()
    else:
        # Пользователь видит только свои заявки, также сортируем
        orders = Order.query.filter_by(user_id=current_user.id).order_by(
            Order.status.asc(),
            Order.created_at.desc()
        ).all()

    # Преобразуем в словари с правильными данными о машине
    orders_data = []
    for order in orders:
        order_dict = order.to_dict()
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

    applicant = data.get("applicant") or current_user.full_name or "Не указан"
    department = data.get("department") or current_user.department or "Не указан"
    phone_number = data.get("phone_number") or current_user.phone_number

    # УДАЛЯЕМ проверку на одинаковый тип тента
    draft_cargos = DraftCargo.query.filter_by(user_id=current_user.id).all()

    if not draft_cargos:
        return jsonify({"error": "Нет грузов в заявке"}), 400

    # Обрабатываем желаемое время отправления
    preferred_departure_time = None
    if data.get("preferred_departure_time"):
        try:
            time_str = data["preferred_departure_time"]
            if ":" in time_str and len(time_str.split(":")) == 2:
                hours, minutes = map(int, time_str.split(":"))
                preferred_departure_time = datetime.combine(
                    datetime.now().date(),
                    time(hour=hours, minute=minutes)
                )
            else:
                preferred_departure_time = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        except Exception as e:
            return jsonify({"error": f"Неверный формат времени: {str(e)}"}), 400

    # Создаём заявку с привязкой к пользователю
    order = Order(
        applicant=applicant,
        department=department,
        phone_number=phone_number,
        # УДАЛЯЕМ: tent_type=tent_type,
        status="new",
        user_id=current_user.id,
        preferred_departure_time=preferred_departure_time
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
            quantity=draft.quantity,
            departure=draft.departure,
            destination=draft.destination,
            tent_type=draft.tent_type,  # Сохраняем тип тента груза
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
    cargo = DraftCargo(
        name=data.get("name"),
        weight=data.get("weight"),
        length=data.get("length"),
        width=data.get("width"),
        height=data.get("height"),
        quantity=data.get("quantity"),
        departure=data.get("departure"),
        destination=data.get("destination"),
        tent_type=data.get("tent_type", "closed"),  # Добавляем тип тента
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

    # Берем тип тента из первого груза
    required_tent_type = cargo_list[0].get("tent_type", "closed")

    total_weight = sum(c["weight"] * c["quantity"] for c in cargo_list)
    max_l = max(c["length"] for c in cargo_list)
    max_w = max(c["width"] for c in cargo_list)
    max_h_single = max(c["height"] for c in cargo_list)

    print(f"[DEBUG] Order #{order_id} - required tent type: {required_tent_type}")
    print(f"[DEBUG] Total weight: {total_weight}, max dimensions: {max_l}x{max_w}x{max_h_single}")

    def can_stack_in_height(cargos, v_height):
        # Преобразуем в плоский список высот (каждая единица груза отдельно)
        heights = []
        for c in cargos:
            for _ in range(c["quantity"]):
                heights.append(c["height"])
        heights.sort(reverse=True)

        # Простая проверка: все грузы должны помещаться по высоте
        # Можно улучшить логику штабелирования при необходимости
        return all(h <= v_height for h in heights)

    # Ищем машины с указанным типом тента
    vehicles = Vehicle.query.filter(
        Vehicle.status == "free",
        Vehicle.tent_type == required_tent_type,
        Vehicle.status != "in_repair"
    ).all()

    print(f"[DEBUG] Found {len(vehicles)} vehicles with tent_type='{required_tent_type}' and status='free':")
    for v in vehicles:
        print(f"  - {v.garage_number} ({v.brand}): {v.capacity}kg, {v.length}x{v.width}x{v.height}m")

    best = None
    min_extra = float("inf")
    suitable_vehicles = []

    for v in vehicles:
        if (v.capacity >= total_weight and
            v.length >= max_l and
            v.width >= max_w):

            height_check = v.height >= max_h_single or can_stack_in_height(cargo_list, v.height)

            if height_check:
                extra = v.capacity - total_weight
                suitable_vehicles.append(v)
                if extra < min_extra:
                    min_extra = extra
                    best = v
                print(f"[DEBUG] Vehicle {v.garage_number} is suitable (extra: {extra}kg)")
            else:
                print(f"[DEBUG] Vehicle {v.garage_number} failed height check: {v.height} < {max_h_single}")
        else:
            print(f"[DEBUG] Vehicle {v.garage_number} failed capacity/dimensions check: {v.capacity}kg/{v.length}x{v.width}m vs required {total_weight}kg/{max_l}x{max_w}m")

    if best:
        return jsonify(best.to_dict())

    print(f"[DEBUG] No suitable vehicles with tent_type='{required_tent_type}'. Searching all free vehicles...")

    # Если не нашли машину с нужным типом тента, ищем любую доступную
    all_vehicles = Vehicle.query.filter(
        Vehicle.status == "free",
        Vehicle.status != "in_repair"
    ).all()

    for v in all_vehicles:
        if (v.capacity >= total_weight and
            v.length >= max_l and
            v.width >= max_w):

            height_check = v.height >= max_h_single or can_stack_in_height(cargo_list, v.height)

            if height_check:
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
    return jsonify({"error": f"Подходящая машина не найдена. Требования: {total_weight}кг, {max_l}x{max_w}x{max_h_single}м"}), 404


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
            Order.preferred_departure_time.asc()
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
    """Преобразование статуса в читаемый текст"""
    status_map = {
        "new": "Новая",
        "assigned": "Назначена",
        "completed": "Завершена",
        "in_progress": "В пути",
    }
    return status_map.get(status, status)

@app.route("/export_trips", methods=["GET"])
@login_required
def export_trips():
    """Экспорт истории рейсов в Excel"""
    try:
        # Собираем фильтры из запроса
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

        # Получаем все отфильтрованные рейсы
        trips = query.order_by(Trip.started_at.desc()).all()

        # Создаем Excel файл
        wb = Workbook()
        ws = wb.active
        ws.title = "История рейсов"

        # Заголовки
        headers = [
            "ID рейса", "ID заявки", "Дата начала", "Дата завершения",
            "Продолжительность", "Гос. номер", "Водитель", "Марка",
            "Гаражный номер", "Тип тента", "Статус",
            "Пройдено км", "Расход топлива", "Примечания",
            "Заявитель", "Отдел", "Телефон",
            "Количество грузов", "Общий вес (кг)", "Общий объем (м³)",
            "Маршруты"
        ]
        ws.append(headers)

        # Данные
        for trip in trips:
            # Продолжительность
            duration = ""
            if trip.started_at and trip.completed_at:
                start = trip.started_at.replace(tzinfo=None) if isinstance(trip.started_at, datetime) else trip.started_at
                end = trip.completed_at.replace(tzinfo=None) if isinstance(trip.completed_at, datetime) else trip.completed_at
                diff = end - start
                hours = diff.total_seconds() // 3600
                minutes = (diff.total_seconds() % 3600) // 60
                duration = f"{int(hours)}ч {int(minutes)}м"

            # Информация о заказе
            order = trip.order
            vehicle = trip.vehicle

            # Статистика по грузам
            cargo_count = 0
            total_weight = 0
            total_volume = 0
            routes = []

            if order and order.cargos:
                cargo_count = len(order.cargos)
                total_weight = sum(c.weight * c.quantity for c in order.cargos)
                total_volume = sum(c.length * c.width * c.height * c.quantity for c in order.cargos)
                routes = list(set(f"{c.departure} → {c.destination}" for c in order.cargos))

            # Статус на русском
            status_text = {
                "completed": "Завершен",
                "in_progress": "В пути",
                "cancelled": "Отменен"
            }.get(trip.status, trip.status)

            # Тип тента
            tent_type = "Закрытый" if vehicle and vehicle.tent_type == "closed" else "Открытый" if vehicle and vehicle.tent_type == "open" else ""

            # Форматируем даты
            started_at = trip.started_at.strftime("%d.%m.%Y %H:%M") if trip.started_at else ""
            completed_at = trip.completed_at.strftime("%d.%m.%Y %H:%M") if trip.completed_at else ""

            # Добавляем строку
            row = [
                trip.id,
                trip.order_id,
                started_at,
                completed_at,
                duration,
                vehicle.gos_number if vehicle else "",
                vehicle.driver if vehicle else "",
                vehicle.brand if vehicle else "",
                vehicle.garage_number if vehicle else "",
                tent_type,
                status_text,
                trip.distance_km or "",
                trip.fuel_consumed or "",
                trip.notes or "",
                order.applicant if order else "",
                order.department if order else "",
                order.phone_number if order else "",
                cargo_count,
                round(total_weight, 2),
                round(total_volume, 2),
                "\n".join(routes) if routes else ""
            ]
            ws.append(row)

        # Автоподбор ширины столбцов
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width

        # Сохраняем в буфер
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        # Определяем имя файла
        filename = f"История_рейсов_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.xlsx"

        # Отправляем файл
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        app.logger.error(f"Ошибка при экспорте истории рейсов: {str(e)}")
        return jsonify({"error": f"Ошибка при экспорте: {str(e)}"}), 500

@app.route("/export_orders")
def export_orders():
    orders = Order.query.all()
    wb: Workbook = Workbook()
    ws: Worksheet = wb.active or wb.create_sheet("Рейсы")
    ws.title = "Рейсы"
    ws.append(["ID", "Создано", "Желаемое время", "Статус", "Водитель", "Гос. номер", "Грузов", "Общий вес"])
    for o in orders:
        created = o.created_at.strftime("%d.%m.%Y %H:%M") if o.created_at else "-"

        # Форматируем желаемое время
        preferred_time = "-"
        if o.preferred_departure_time:
            preferred_time = o.preferred_departure_time.strftime("%H:%M")

        status = get_status_text(o.status)
        driver = o.vehicle.driver if o.vehicle else "-"
        gos_number = o.vehicle.gos_number if o.vehicle else "-"
        cargo_count = len(o.cargos)
        total_weight = sum(c.weight * c.quantity for c in o.cargos) if o.cargos else 0
        ws.append([o.id, created, preferred_time, status, driver, gos_number, cargo_count, total_weight])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="reyisy.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def create_pdf_from_html(html_content):
    """Создание PDF из HTML контента"""
    pdf = BytesIO()

    # Создаем контекст с указанием шрифта
    context = {
        'fontName': font_name,
    }

    # Конвертируем HTML в PDF
    pisa_status = pisa.CreatePDF(
        BytesIO(html_content.encode('UTF-8')),
        dest=pdf,
        encoding='UTF-8'
    )

    if pisa_status.err:
        raise Exception(f"Ошибка генерации PDF: {pisa_status.err}")

    pdf.seek(0)
    return pdf


def register_fonts():
    """Регистрация TTF шрифтов"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)

        # Пути к TTF шрифтам
        ttf_fonts = [
            os.path.join(project_root, 'fonts', 'arial.ttf'),
            os.path.join(project_root, 'fonts', 'timesnewromanpsmt.ttf'),
            os.path.join(project_root, 'fonts', 'timesbd.ttf'),  # Times New Roman Bold
            r'C:\Windows\Fonts\times.ttf',
            r'C:\Windows\Fonts\timesbd.ttf',
        ]

        for font_path in ttf_fonts:
            if os.path.exists(font_path):
                try:
                    font_name = os.path.splitext(os.path.basename(font_path))[0]
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    print(f"Зарегистрирован шрифт: {font_name}")
                    return font_name
                except Exception as e:
                    print(f"Ошибка регистрации {font_path}: {e}")

        return "Times-Roman"
    except Exception as e:
        print(f"Ошибка: {e}")
        return "Times-Roman"




font_name = register_fonts()

@app.route("/debug_paths", methods=["GET"])
def debug_paths():
    """Отладочная информация о путях"""
    import sys
    import inspect

    info = {
        "current_file": __file__,
        "current_dir": os.path.dirname(os.path.abspath(__file__)),
        "project_root": os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "sys_path": sys.path,
        "working_dir": os.getcwd(),
    }

    # Проверяем наличие шрифтов
    font_paths = [
        os.path.join(info["project_root"], 'fonts', 'Akrobat-Regular.otf'),
        os.path.join(info["project_root"], 'fonts', 'arial.ttf'),
        os.path.join(info["project_root"], 'fonts', 'Arial.ttf'),
    ]

    info["fonts"] = {}
    for font_path in font_paths:
        info["fonts"][font_path] = {
            "exists": os.path.exists(font_path),
            "size": os.path.getsize(font_path) if os.path.exists(font_path) else None,
        }

    return jsonify(info)

def check_project_structure():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Текущая директория: {current_dir}")
    print(f"Содержимое текущей директории:")
    for item in os.listdir(current_dir):
        print(f"  - {item}")

    fonts_dir = os.path.join(current_dir, 'fonts')
    print(f"\nПапка fonts существует: {os.path.exists(fonts_dir)}")
    if os.path.exists(fonts_dir):
        print("Файлы в папке fonts:")
        for item in os.listdir(fonts_dir):
            print(f"  - {item}")

@app.route("/route_sheet/<int:order_id>", methods=["GET"])
def print_route_sheet(order_id):
    """Печать маршрутного листа заявки"""
    try:
        order = Order.query.get_or_404(order_id)

        if not order.vehicle:
            return jsonify({"error": "На заявку не назначена машина"}), 400

        if order.status != "assigned":
            return jsonify({"error": "Маршрутный лист можно печатать только для назначенных заявок"}), 400

        # Формируем данные для маршрутного листа
        vehicle = order.vehicle
        cargos = order.cargos

        # Общий вес
        total_weight = sum(c.weight * c.quantity for c in cargos)

        # Получаем все уникальные адреса из грузов
        addresses = []
        for cargo in cargos:
            if cargo.destination not in addresses:
                addresses.append(cargo.destination)

        # Дата назначения
        assignment_date = datetime.now().strftime("%d.%m.%Y")
        if order.created_at:
            assignment_date = order.created_at.strftime("%d.%m.%Y")

        # Форматируем время отправления
        preferred_time = ""
        if order.preferred_departure_time:
            time_obj = order.preferred_departure_time
            if isinstance(time_obj, str):
                time_obj = datetime.fromisoformat(time_obj.replace('Z', '+00:00'))
            preferred_time = time_obj.strftime("%H:%M")

        # Создаем HTML для маршрутного листа с указанием шрифта
        route_sheet_html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
    <title>Маршрутный лист #{order.id}</title>
    <style>
        @page {{
            size: A4;
            margin: 15mm;
        }}
        body {{
            font-family: '{font_name}', Arial, sans-serif;
            margin: 0;
            padding: 0;
            font-size: 12pt;
            line-height: 1.4;
        }}
        .header {{
            text-align: center;
            margin-bottom: 20px;
            border-bottom: 2px solid #000;
            padding-bottom: 10px;
        }}
        .title {{
            font-size: 16pt;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .subtitle {{
            font-size: 14pt;
            margin-bottom: 15px;
        }}
        .info-block {{
            margin: 10px 0;
            font-size: 11pt;
        }}
        .info-label {{
            font-weight: bold;
        }}
        .table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 10pt;
        }}
        .table th, .table td {{
            border: 1px solid #000;
            padding: 5px;
            text-align: left;
            vertical-align: top;
        }}
        .table th {{
            background-color: #f2f2f2;
            font-weight: bold;
            text-align: center;
        }}
        .signature-block {{
            margin-top: 40px;
            display: flex;
            justify-content: space-between;
            page-break-inside: avoid;
        }}
        .signature {{
            width: 45%;
        }}
        .signature-line {{
            border-top: 1px solid #000;
            margin-top: 30px;
            padding-top: 5px;
        }}
        .footer {{
            margin-top: 20px;
            font-size: 9pt;
            color: #666;
            text-align: center;
        }}
        .page-break {{
            page-break-before: always;
        }}
        .nowrap {{
            white-space: nowrap;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="title">marshrut</div>
        <div class="subtitle">к путевому листу № {order.id} от {assignment_date}</div>
    </div>

    <div class="info-block">
        <div><span class="info-label">Водитель:</span> {vehicle.driver}</div>
        <div><span class="info-label">Машина:</span> {vehicle.brand}, {vehicle.gos_number} (гаражный №{vehicle.garage_number})</div>
        <div><span class="info-label">Тип тента:</span> {"Открытый" if vehicle.tent_type == "open" else "Закрытый"}</div>
        <div><span class="info-label">Заявитель:</span> {order.applicant}</div>
        <div><span class="info-label">Отдел:</span> {order.department}</div>
        <div><span class="info-label">Телефон:</span> {order.phone_number or "Не указан"}</div>
        <div><span class="info-label">Желаемое время отправления:</span> {preferred_time or "Не указано"}</div>
        <div><span class="info-label">Примечание:</span> {order.note or "Нет"}</div>
    </div>

    <table class="table">
        <thead>
            <tr>
                <th>№</th>
                <th>Заявка</th>
                <th>Адрес доставки</th>
                <th>Планируемое прибытие</th>
                <th>Время работы</th>
                <th>Вес, кг</th>
                <th>Телефон</th>
                <th>Комментарий</th>
                <th>Примечание</th>
            </tr>
        </thead>
        <tbody>"""

        # Добавляем строки с грузами
        for i, cargo in enumerate(cargos, 1):
            route_sheet_html += f"""
            <tr>
                <td class="nowrap">{i}</td>
                <td class="nowrap">{order.id}</td>
                <td>{cargo.destination}</td>
                <td class="nowrap">{preferred_time or "По графику"}</td>
                <td class="nowrap">1 час</td>
                <td class="nowrap">{cargo.weight * cargo.quantity}</td>
                <td class="nowrap">{order.phone_number or "Не указан"}</td>
                <td>{cargo.name} - {cargo.quantity} мест</td>
                <td class="nowrap">{"Открытый" if cargo.tent_type == "open" else "Закрытый"}</td>
            </tr>"""

        # Итоговая строка
        route_sheet_html += f"""
            <tr>
                <td colspan="5" style="text-align: right; font-weight: bold;">ИТОГО:</td>
                <td style="font-weight: bold;">{total_weight} кг</td>
                <td colspan="3"></td>
            </tr>
        </tbody>
    </table>

    <div class="info-block">
        <div><span class="info-label">Общий вес груза:</span> {total_weight} кг</div>
        <div><span class="info-label">Количество грузов:</span> {len(cargos)}</div>
        <div><span class="info-label">Маршрут:</span> {cargos[0].departure if cargos else ""} → {", ".join(addresses)}</div>
    </div>

    <div class="signature-block">
        <div class="signature">
            <div>Логистик выдал:</div>
            <div class="signature-line"></div>
            <div style="text-align: center; margin-top: 5px;">(подпись)</div>
            <div style="text-align: center; margin-top: 10px;">(447756085)</div>
        </div>

        <div class="signature">
            <div>Водитель сдал:</div>
            <div class="signature-line"></div>
            <div style="text-align: center; margin-top: 5px;">(подпись)</div>
            <div style="text-align: center; margin-top: 10px;">{vehicle.driver}</div>
        </div>
    </div>

    <div class="footer">
        <div>Сформировано: {datetime.now().strftime("%d.%m.%Y %H:%M")}</div>
        <div>Статус: {get_status_text(order.status)}</div>
        <div>Система логистики САЗ</div>
    </div>
</body>
</html>"""

        # Генерируем PDF
        pdf = create_pdf_from_html(route_sheet_html)

        # Создаем ответ
        response = make_response(pdf.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        filename = f'маршрутный_лист_{order.id}.pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{quote(filename)}"'

        return response

    except Exception as e:
        app.logger.error(f"Ошибка при генерации маршрутного листа: {str(e)}")
        return jsonify({"error": f"Ошибка при генерации маршрутного листа: {str(e)}"}), 500





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
    if "preferred_departure_time" in data:
        if data["preferred_departure_time"]:
            try:
                time_str = data["preferred_departure_time"]
                if ":" in time_str and len(time_str.split(":")) == 2:
                    hours, minutes = map(int, time_str.split(":"))
                    order.preferred_departure_time = datetime.combine(
                        datetime.now().date(),
                        time(hour=hours, minute=minutes)
                    )
                else:
                    order.preferred_departure_time = datetime.fromisoformat(
                        data["preferred_departure_time"].replace("Z", "+00:00")
                    )
            except Exception as e:
                return jsonify({"error": f"Неверный формат времени: {str(e)}"}), 400
        else:
            order.preferred_departure_time = None

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
    return send_file(os.path.join(_static_root, "index.html"))

@app.route("/index.html")
def index_html():
    return send_file(os.path.join(_static_root, "index.html"))

@app.route("/login.html")
def login_html():
    return send_file(os.path.join(_static_root, "login.html"))

@app.route("/admin.html")
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
    """Проверяет заявки, у которых подходит срок отправления"""
    while True:
        with app.app_context():
            now = datetime.now(timezone.utc)
            urgent_orders = Order.query.filter(
                Order.status == 'new',
                Order.preferred_departure_time != None,
                Order.preferred_departure_time <= now + timedelta(hours=2)
            ).all()

            for order in urgent_orders:
                # Можно отправить уведомление
                print(f"СРОЧНО: Заявка #{order.id} требует отправления в {order.preferred_departure_time}")

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

    # Сортировка по дате начала (новые сверху) и без пагинации
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
