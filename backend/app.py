import os
from itertools import permutations

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure SQLAlchemy
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    basedir, "database.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


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


# API Routes


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


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Создать таблицы, если они не существуют
    app.run(debug=True, port=5000)
