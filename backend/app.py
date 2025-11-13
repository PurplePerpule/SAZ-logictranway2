import os

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
        }


class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(100), nullable=False)
    driver = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Float, nullable=False)  # in kg
    status = db.Column(
        db.String(50), nullable=False, default="free"
    )  # 'free' or 'busy'

    def to_dict(self):
        return {
            "id": self.id,
            "brand": self.brand,
            "driver": self.driver,
            "capacity": self.capacity,
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
    new_cargo = Cargo(
        name=data["name"],
        weight=data["weight"],
        length=data["length"],
        width=data["width"],
        quantity=data["quantity"],
        departure=data["departure"],
        destination=data["destination"],
    )
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
    new_vehicle = Vehicle(
        brand=data["brand"],
        driver=data["driver"],
        capacity=data["capacity"],
        status=data.get("status", "free"),
    )
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
    cargos = data.get("cargos", [])  # List of cargo dicts or IDs

    # Считаем общую массу грузов
    total_weight = sum(cargo["weight"] * cargo["quantity"] for cargo in cargos)

    # Ищем подходящую машину
    suitable_vehicle = Vehicle.query.filter(
        Vehicle.status == "free", Vehicle.capacity >= total_weight
    ).first()

    if suitable_vehicle:
        # Optionally mark as busy (for prototype, we'll just return it)
        # suitable_vehicle.status = 'busy'
        # db.session.commit()
        return jsonify(
            {
                "message": "Suitable vehicle found",
                "vehicle": suitable_vehicle.to_dict(),
                "total_weight": total_weight,
            }
        )
    else:
        return jsonify({"message": "No suitable vehicle found"}), 404


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Создать таблицы, если они не существуют
    app.run(debug=True, port=5000)
