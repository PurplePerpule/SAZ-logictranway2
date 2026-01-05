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

    user = db.relationship('User', backref='draft_cargos')

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
    tent_type = db.Column(db.String(20), nullable=False, default="closed")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Новое поле: желаемое время отправления
    preferred_departure_time = db.Column(db.DateTime, nullable=True)

    vehicle: Mapped["Vehicle"] = relationship("Vehicle", backref="orders")
    cargos: Mapped[List["Cargo"]] = relationship(
        "Cargo", secondary=order_cargo, backref="orders", lazy="joined"
    )
    user = db.relationship('User', backref='orders')

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
            "tent_type": self.tent_type,
            "preferred_departure_time": self.preferred_departure_time.isoformat() if self.preferred_departure_time else None,
            "user_id": self.user_id,
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


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    full_name = db.Column(db.String(100), nullable=True)  # Полное имя пользователя
    department = db.Column(db.String(100), nullable=True)  # Отдел пользователя
    phone_number = db.Column(db.String(20), nullable=True)  # Телефон пользователя

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
        orders = Order.query.all()
    else:
        orders = Order.query.filter_by(user_id=current_user.id).all()
    return jsonify([o.to_dict() for o in orders])

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

    # Используем данные из профиля пользователя, если не указаны другие
    applicant = data.get("applicant") or current_user.full_name or "Не указан"
    department = data.get("department") or current_user.department or "Не указан"
    phone_number = data.get("phone_number") or current_user.phone_number
    tent_type = data.get("tent_type", "closed")

    # Обрабатываем желаемое время отправления
    preferred_departure_time = None
    if data.get("preferred_departure_time"):
        try:
            # Парсим строку в формате "HH:MM" или "HH:MM:SS"
            time_str = data["preferred_departure_time"]
            # Если только часы и минуты
            if ":" in time_str and len(time_str.split(":")) == 2:
                hours, minutes = map(int, time_str.split(":"))
                preferred_departure_time = datetime.combine(
                    datetime.now().date(),
                    time(hour=hours, minute=minutes)
                )
            else:
                # Пытаемся парсить как ISO строку
                preferred_departure_time = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        except Exception as e:
            return jsonify({"error": f"Неверный формат времени: {str(e)}"}), 400

    # Создаём заявку с привязкой к пользователю
    order = Order(
        applicant=applicant,
        department=department,
        phone_number=phone_number,
        tent_type=tent_type,
        status="new",
        user_id=current_user.id,
        preferred_departure_time=preferred_departure_time
    )
    db.session.add(order)
    db.session.flush()

    # Копируем грузы из черновика текущего пользователя
    draft_cargos = DraftCargo.query.filter_by(user_id=current_user.id).all()
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
    cargo = DraftCargo(**data, user_id=current_user.id)  # Привязка к пользователю
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

@app.route("/suggest_vehicle/<int:order_id>", methods=["GET"])
def suggest_vehicle(order_id):
    order = Order.query.get_or_404(order_id)
    cargos = order.cargos
    if not cargos:
        return jsonify({"error": "В заявке нет грузов"}), 404

    cargo_list = [c.to_dict() for c in cargos]
    total_weight = sum(c["weight"] * c["quantity"] for c in cargo_list)
    max_l = max(c["length"] for c in cargo_list)
    max_w = max(c["width"] for c in cargo_list)
    max_h_single = max(c["height"] for c in cargo_list)

    print(f"[DEBUG] Order #{order_id} tent_type: {order.tent_type}")
    print(f"[DEBUG] Total weight: {total_weight}, max dimensions: {max_l}x{max_w}x{max_h_single}")

    def can_stack_in_height(cargos, v_height):
        heights = sorted([c["height"] * c["quantity"] for c in cargos], reverse=True)
        total_stacked = 0
        for h in heights:
            if total_stacked + h <= v_height:
                total_stacked += h
            else:
                return False
        return True

    # Ищем машины с указанным типом тента
    vehicles = Vehicle.query.filter(
        Vehicle.status == "free",
        Vehicle.tent_type == order.tent_type,
        Vehicle.status != "in_repair"
    ).all()

    print(f"[DEBUG] Found {len(vehicles)} vehicles with tent_type='{order.tent_type}' and status='free':")
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

    print(f"[DEBUG] No suitable vehicles with tent_type='{order.tent_type}'. Searching all free vehicles...")

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
            "warning": f"Не найдена машина с типом тента '{order.tent_type}'. Предлагается машина с типом тента '{best.tent_type}'"
        })

    print(f"[DEBUG] No suitable vehicles at all")
    return jsonify({"error": f"Подходящая машина не найдена. Требования: {total_weight}кг, {max_l}x{max_w}x{max_h_single}м"}), 404

@app.route("/match", methods=["POST"])
def match_vehicle():
    data = request.get_json()
    cargo_inputs = data.get("cargos", [])
    tent_type = data.get("tent_type", "closed")

    print(f"[DEBUG] Match request: tent_type={tent_type}, cargos={len(cargo_inputs)}")

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

    total_weight = sum(c["weight"] * c["quantity"] for c in cargo_list)
    max_l = max(c["length"] for c in cargo_list)
    max_w = max(c["width"] for c in cargo_list)
    max_h_single = max(c["height"] for c in cargo_list)

    print(f"[DEBUG] Total weight: {total_weight}, max dimensions: {max_l}x{max_w}x{max_h_single}")

    def can_stack_in_height(cargos, vehicle_height):
        heights = sorted([c["height"] * c["quantity"] for c in cargos], reverse=True)
        total_stacked_height = 0
        for h in heights:
            if total_stacked_height + h <= vehicle_height:
                total_stacked_height += h
            else:
                return False
        return True

    # Сначала ищем машины с указанным типом тента
    suitable_vehicles = Vehicle.query.filter(
        Vehicle.status == "free",
        Vehicle.capacity >= total_weight,
        Vehicle.length >= max_l,
        Vehicle.width >= max_w,
        Vehicle.tent_type == tent_type,
        Vehicle.status != "in_repair"
    ).all()

    print(f"[DEBUG] Found {len(suitable_vehicles)} vehicles with tent_type='{tent_type}'")

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
            "warning": f"Не найдена машина с типом тента '{tent_type}'. Предлагается машина с типом тента '{best_vehicle.tent_type}'",
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
        },
    }), 404

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

@app.route("/ttn/<int:order_id>", methods=["GET"])
def print_ttn(order_id):
    order = Order.query.get_or_404(order_id)
    if not order.vehicle:
        return jsonify({"error": "Нет машины"}), 400
    total_weight = sum(c.weight * c.quantity for c in order.cargos)
    cargos_html = "".join([f"<tr><td>{c.name}</td><td>{c.quantity}</td><td>{c.weight * c.quantity}</td></tr>" for c in order.cargos])
    ttn_html = f"""<html>
<head>
  <style>
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid black; padding: 8px; }}
    h1 {{ text-align: center; }}
  </style>
</head>
<body>
  <h1>Товарно-транспортная накладная ТТН-1 № {order.id}</h1>
  <p>Дата: {datetime.now().strftime('%d.%m.%Y')}</p>
  <p>Грузоотправитель: ООО "САЗ"</p>
  <p>Грузополучатель: По адресу назначения</p>
  <p>Перевозчик: {order.vehicle.driver}, авто {order.vehicle.brand} ({order.vehicle.gos_number})</p>
  <h2>Товарная часть</h2>
  <table>
    <tr><th>Наименование</th><th>Количество</th><th>Вес</th></tr>
    {cargos_html}
    <tr><th colspan="2">Итого</th><td>{total_weight} кг</td></tr>
  </table>
  <h2>Транспортная часть</h2>
  <p>Пункт погрузки: {order.cargos[0].departure if order.cargos else '-'} </p>
  <p>Пункт разгрузки: {order.cargos[-1].destination if order.cargos else '-'} </p>
  <p>Подпись водителя: ___________________</p>
  <p>Подпись грузоотправителя: ___________________</p>
</body>
</html>"""
    pdf = pdfkit.from_string(ttn_html, False)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=ttn_{order.id}.pdf'
    return response


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
