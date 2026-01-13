from models import User, get_session
import bcrypt

def create_user():
    session = get_session()
    username = "test"
    password = "test"
    
    # Check if user already exists
    existing = session.query(User).filter_by(username=username).first()
    if existing:
        session.delete(existing)
        session.commit()
    
    user = User(username=username, name="Test User", cpf="12345678901", email="test@example.com")
    user.set_password(password)
    session.add(user)
    session.commit()
    print(f"User {username} created successfully.")
    session.close()

if __name__ == "__main__":
    create_user()
