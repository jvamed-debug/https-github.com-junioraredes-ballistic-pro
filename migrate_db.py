import json
import os
from models import User, Firearm, get_session
from datetime import datetime

def migrate_data():
    USER_DATA_FILE = "user_data.json"
    if not os.path.exists(USER_DATA_FILE):
        print("No JSON data to migrate.")
        return

    with open(USER_DATA_FILE, "r") as f:
        data = json.load(f)

    session = get_session()
    
    # Check if a default user already exists to avoid duplicate migration
    existing_user = session.query(User).filter_by(username="admin").first()
    if existing_user:
        print("Migration already completed or user 'admin' exists.")
        session.close()
        return

    # Create a default user for the migrated data
    user = User(username="admin", name=data["user"]["name"], cr=data["user"]["cr"])
    user.set_password("admin123") # Default password for migrated data
    session.add(user)
    session.flush() # Get user ID

    for f_data in data["firearms"]:
        firearm = Firearm(
            user_id=user.id,
            model=f_data["model"],
            sigma=f_data["sigma"],
            craf=f_data["craf"],
            serial=f_data["serial"],
            expiration=datetime.strptime(f_data["expiration"], "%Y-%m-%d").date()
        )
        session.add(firearm)

    session.commit()
    session.close()
    print("Migration successful. User 'admin' created with password 'admin123'.")

if __name__ == "__main__":
    migrate_data()
