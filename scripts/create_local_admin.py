"""Create or update a local AURIX administrator for development."""

from __future__ import annotations

import getpass
import json
import sys
from pathlib import Path

# Ensure the repository root is importable when this file is executed
# directly as: python .\scripts\create_local_admin.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.orm import Session

from aurix_api.routers.auth import hash_password
from aurix_core.database.engine import SessionLocal, Base, engine
from aurix_core.database.models.auth import Tenant, User


def main() -> int:
    print("AURIX local administrator setup")
    print("--------------------------------")

    tenant_id = input("Tenant ID [ENTERPRISE_GLOBAL]: ").strip() or "ENTERPRISE_GLOBAL"
    email = input("Admin email [executive@aurix.ai]: ").strip().lower() or "executive@aurix.ai"
    full_name = input("Full name [AURIX Executive]: ").strip() or "AURIX Executive"

    password = input("Password: ")
    confirm = input("Confirm password: ")

    if not password:
        print("Password cannot be empty.")
        return 1

    if password != confirm:
        print("Passwords do not match.")
        return 1

    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    try:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

        if not tenant:
            tenant = Tenant(
                id=tenant_id,
                name=tenant_id,
            )
            db.add(tenant)
            db.flush()

        permissions = [
            "READ_DATA",
            "RUN_ANALYSIS",
            "WRITE_DATA",
            "USE_AI",
            "VIEW_FINANCIALS",
        ]

        user = db.query(User).filter(User.email == email).first()

        if user:
            user.full_name = full_name
            user.hashed_password = hash_password(password)
            user.role = "EXECUTIVE"
            user.tenant_id = tenant_id
            user.permissions_json = json.dumps(permissions)
            user.is_active = True
        else:
            user = User(
                id="USR-LOCAL-EXECUTIVE",
                email=email,
                full_name=full_name,
                hashed_password=hash_password(password),
                role="EXECUTIVE",
                tenant_id=tenant_id,
                permissions_json=json.dumps(permissions),
                is_active=True,
            )
            db.add(user)

        db.commit()

        print("")
        print("User created/updated successfully.")
        print(f"Email:  {email}")
        print(f"Tenant: {tenant_id}")
        print("Role:   EXECUTIVE")

    finally:
        db.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())


