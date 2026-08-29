from fastapi import APIRouter, HTTPException, Header, status, Depends
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
import datetime
import hmac
import hashlib
import json
import base64
import os
import uuid

from aurix_core.config.settings import settings
from aurix_core.database.engine import get_db
from aurix_core.database.models.auth import User, Tenant
from aurix_core.database.tenant_context import set_current_tenant_id

router = APIRouter(prefix="/auth", tags=["Authentication & Identity"])

PBKDF2_ITERATIONS = 600000

def _get_signing_key() -> str:
    secret = settings.api_secret_key.strip()
    return secret if secret else "aurix-enterprise-production-fallback-key-2026"

def hash_password(password: str) -> str:
    """Computes a cryptographically secure salted PBKDF2-HMAC-SHA256 hash."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a password against the salted hash, with backward-compatibility check."""
    if hashed_password.startswith("pbkdf2_sha256$"):
        parts = hashed_password.split("$")
        if len(parts) != 4:
            return False
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected_key = parts[3]
        computed_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations).hex()
        return hmac.compare_digest(computed_key, expected_key)
    # Legacy SHA-256 fallback compatibility check
    legacy_hash = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(legacy_hash, hashed_password)

# --- Schemas ---

class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    tenantId: Optional[str] = Field(default=None, description="Target Tenant ID")

class SignupRequest(BaseModel):
    email: EmailStr = Field(..., description="Corporate email address")
    password: str = Field(..., min_length=8, description="Account password (min 8 chars)")
    fullName: str = Field(..., min_length=2, description="User full name")
    organizationName: str = Field(..., min_length=2, description="Company / Organization Name")

class InviteUserRequest(BaseModel):
    email: EmailStr = Field(..., description="Invitee email address")
    fullName: str = Field(..., description="Invitee full name")
    role: str = Field(default="SUPPLY_CHAIN_ANALYST", description="Platform RBAC role")

class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., description="Account email address")
    currentPassword: str = Field(..., description="Current password")
    newPassword: str = Field(..., min_length=8, description="New password (min 8 chars)")

class UserProfile(BaseModel):
    userId: str
    email: str
    fullName: str
    role: str
    tenantId: str
    permissions: List[str]

class LoginResponse(BaseModel):
    token: str
    user: UserProfile
    expiresInSeconds: int

# --- Token Management ---

def create_session_token(user: User, tenant_id: str) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    exp = now + datetime.timedelta(minutes=settings.api_access_token_expire_minutes)
    payload = {
        "userId": user.id,
        "email": user.email,
        "role": user.role,
        "tenantId": tenant_id,
        "iat": now.timestamp(),
        "exp": exp.timestamp()
    }
    raw_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
    b64_payload = base64.urlsafe_b64encode(raw_bytes).decode("utf-8")
    signature = hmac.new(_get_signing_key().encode("utf-8"), b64_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"aurix.{b64_payload}.{signature}"

def verify_session_token(token: str) -> Dict:
    try:
        parts = token.split(".")
        if len(parts) != 3 or parts[0] != "aurix":
            raise ValueError("Malformed token format")
        b64_payload, signature = parts[1], parts[2]
        expected_sig = hmac.new(_get_signing_key().encode("utf-8"), b64_payload.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            raise ValueError("Invalid token signature")
        payload = json.loads(base64.urlsafe_b64decode(b64_payload.encode("utf-8")).decode("utf-8"))
        if payload.get("exp", 0) < datetime.datetime.now(datetime.timezone.utc).timestamp():
            raise ValueError("Session expired")
        return payload
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Authentication failed: {str(e)}")

def get_current_user_claims(authorization: Optional[str] = Header(None)) -> Dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Bearer authorization header.")
    token = authorization.replace("Bearer ", "").strip()
    claims = verify_session_token(token)
    
    # Propagate tenant identity to execution context
    tenant_id = claims.get("tenantId")
    if tenant_id:
        set_current_tenant_id(tenant_id)
        
    return claims

def _bootstrap_initial_system_if_empty(db: Session):
    """Seeds the initial super admin ONLY if the database is completely empty."""
    if db.query(Tenant).count() == 0:
        default_tenant = Tenant(id=settings.default_tenant_id, name="Quidch Apparel Private Limited (Global)")
        db.add(default_tenant)
        
        super_admin = User(
            id="USR-AURIX-001",
            email="kaushik@aurix.ai",
            full_name="Kaushik Jain",
            hashed_password=hash_password("Aurix@2026"),
            role="SUPER_ADMIN",
            tenant_id=default_tenant.id,
            permissions_json=json.dumps(["*"])
        )
        db.add(super_admin)
        
        planner = User(
            id="USR-AURIX-002",
            email="planner.blr@aurix.ai",
            full_name="Bengaluru SC Planner",
            hashed_password=hash_password("Aurix@2026"),
            role="PLANNER",
            tenant_id=default_tenant.id,
            permissions_json=json.dumps(["DATA:*", "INVENTORY:*", "PROCUREMENT:*", "MANUFACTURING:*"])
        )
        db.add(planner)
        db.commit()

# --- Endpoints ---

@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    email_clean = req.email.strip().lower()
    if not email_clean:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required.")
    
    _bootstrap_initial_system_if_empty(db)
    
    user = db.query(User).filter(User.email == email_clean).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account has been deactivated.")
    
    if not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    
    # Auto-upgrade legacy hash on successful login
    if not user.hashed_password.startswith("pbkdf2_sha256$"):
        user.hashed_password = hash_password(req.password)

    user.last_login_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()

    tenant_scope = req.tenantId or user.tenant_id
    token = create_session_token(user, tenant_scope)
    permissions = json.loads(user.permissions_json) if user.permissions_json else ["*"]

    return LoginResponse(
        token=token,
        user=UserProfile(
            userId=user.id,
            email=user.email,
            fullName=user.full_name,
            role=user.role,
            tenantId=tenant_scope,
            permissions=permissions
        ),
        expiresInSeconds=settings.api_access_token_expire_minutes * 60
    )

@router.post("/signup", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def signup(req: SignupRequest, db: Session = Depends(get_db)):
    email_clean = req.email.strip().lower()
    
    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")
    
    tenant_id = f"TNT-{uuid.uuid4().hex[:8].upper()}"
    new_tenant = Tenant(id=tenant_id, name=req.organizationName.strip())
    db.add(new_tenant)
    
    user_id = f"USR-{uuid.uuid4().hex[:8].upper()}"
    new_user = User(
        id=user_id,
        email=email_clean,
        full_name=req.fullName.strip(),
        hashed_password=hash_password(req.password),
        role="SUPER_ADMIN",
        tenant_id=tenant_id,
        permissions_json=json.dumps(["*"]),
        is_active=True
    )
    db.add(new_user)
    db.commit()

    token = create_session_token(new_user, tenant_id)
    return LoginResponse(
        token=token,
        user=UserProfile(
            userId=new_user.id,
            email=new_user.email,
            fullName=new_user.full_name,
            role=new_user.role,
            tenantId=tenant_id,
            permissions=["*"]
        ),
        expiresInSeconds=settings.api_access_token_expire_minutes * 60
    )

@router.get("/me", response_model=UserProfile)
async def get_current_user(claims: Dict = Depends(get_current_user_claims), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == claims["userId"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User record no longer exists.")

    permissions = json.loads(user.permissions_json) if user.permissions_json else ["*"]
    
    return UserProfile(
        userId=user.id,
        email=user.email,
        fullName=user.full_name,
        role=user.role,
        tenantId=claims["tenantId"],
        permissions=permissions
    )

@router.post("/invite", status_code=status.HTTP_201_CREATED)
async def invite_user(
    req: InviteUserRequest,
    claims: Dict = Depends(get_current_user_claims),
    db: Session = Depends(get_db)
):
    if claims.get("role") not in ("SUPER_ADMIN", "ADMIN"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Tenant Admins can issue invitations.")
    
    tenant_id = claims["tenantId"]
    email_clean = req.email.strip().lower()
    
    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already registered in the platform.")

    temp_password = f"AurixTemp!{uuid.uuid4().hex[:6]}"
    new_user = User(
        id=f"USR-{uuid.uuid4().hex[:8].upper()}",
        email=email_clean,
        full_name=req.fullName.strip(),
        hashed_password=hash_password(temp_password),
        role=req.role,
        tenant_id=tenant_id,
        permissions_json=json.dumps(["DATA:*", "INVENTORY:*", "FORECAST:*"]),
        is_active=True
    )
    db.add(new_user)
    db.commit()

    return {
        "success": True,
        "userId": new_user.id,
        "email": new_user.email,
        "temporaryActivationCode": temp_password,
        "tenantId": tenant_id
    }

@router.post("/password/reset")
async def reset_password(
    req: PasswordResetRequest,
    claims: Dict = Depends(get_current_user_claims),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == claims["userId"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    if not verify_password(req.currentPassword, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password incorrect.")

    user.hashed_password = hash_password(req.newPassword)
    db.commit()
    return {"success": True, "message": "Password updated successfully."}

@router.post("/logout")
async def logout(claims: Dict = Depends(get_current_user_claims)):
    return {"success": True, "message": "Session terminated successfully."}