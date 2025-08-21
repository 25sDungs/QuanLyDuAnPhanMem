from src.models import *
from app import app, db
import sys
import os

if __name__ == '__main__':
    with app.app_context():
        print("Creating tables...")
        db.create_all()

        print("Tables created successfully!")

        db.session.commit()
        print("Sample data added!")
