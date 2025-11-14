import os

from app import app, db

# Get the path to the database file
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "database.db")

# Delete the old database file if it exists
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Old database deleted: {db_path}")
else:
    print("No existing database found.")

# Create new database with updated schema
with app.app_context():
    db.create_all()
    print("New database created with updated schema!")
    print("Run 'python init_db.py' to populate with sample data.")
