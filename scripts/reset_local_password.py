from sqlalchemy.orm import Session
from aurix_core.database.engine import SessionLocal
from aurix_core.database.models.auth import User
from aurix_api.routers.auth import hash_password

email = "kaushikjain@gmail.com"
password = input("New password: ")

db: Session = SessionLocal()

try:
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise SystemExit(f"User not found: {email}")

    user.hashed_password = hash_password(password)
    user.is_active = True

    db.commit()

    print("Password reset successfully.")
    print(f"Email: {user.email}")
    print(f"Tenant: {user.tenant_id}")
finally:
    db.close()
