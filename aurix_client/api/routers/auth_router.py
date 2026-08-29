from fastapi import APIRouter, HTTPException, Header, status, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import datetime
import hmac
import hashlib
import json
import base64

router = APIRouter(prefix="/auth", tags=["Authentication"])

SECRET_KEY = "aurix-enterprise-production-secret-key-do-not-expose"

# Deterministic User Directory with pre-computed SHA-256 password hashes
# Default password for all seeded accounts: "Aurix@2026"
DEFAULT_PW_HASH = hashlib.sha256("Aurix@2026".encode()).hexdigest()

USER_DATABASE: Dict[str, Dict] = {
    "kaushik@aurix.ai": {
        "userId": "USR-001",
        "email": "kaushik@aurix.ai",
        "fullName": "Kaushik Jain",
        "role": "SUPER_ADMIN",
        "tenantId": "ENTERPRISE_GLOBAL",
        "passwordHash": DEFAULT_PW_HASH,
        "permissions": ["*"]
    },
    "executive@aurix.ai": {
        "userId": "USR-002",
        "email": "executive@aurix.ai",
        "fullName": "Executive Operator",
        "role": "EXECUTIVE",
        "tenantId": "ENTERPRISE_GLOBAL",
        "passwordHash": DEFAULT_PW_HASH,
        "permissions": ["DECISIONS:*", "ACTIONS:APPROVE", "INTELLIGENCE:READ", "CONTROL_TOWER:READ"]
    },
    "planner.blr@aurix.ai": {
        "userId": "USR-003",
        "email": "planner.blr@aurix.ai",
        "fullName": "Bengaluru SC Planner",
        "role": "PLANNER",
        "tenantId": "ENTERPRISE_GLOBAL",
        "passwordHash": DEFAULT_PW_HASH,
        "permissions": ["DATA:*", "INVENTORY:*", "PROCUREMENT:*", "MANUFACTURING:*"]
    }
}

class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: Optional[str] = Field(default="Aurix@2026", description="User password")
    tenantId: Optional[str] = Field(default="ENTERPRISE_GLOBAL", description="Target Tenant ID")

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

def create_session_token(user: Dict, tenant_id: str) -> str:
    payload = {
        "userId": user["userId"],
        "email": user["email"],
        "role": user["role"],
        "tenantId": tenant_id,
        "exp": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)).timestamp()
    }
    raw_bytes = json.dumps(payload, sort_keys=True).encode()
    b64_payload = base64.urlsafe_b64encode(raw_bytes).decode()
    signature = hmac.new(SECRET_KEY.encode(), b64_payload.encode(), hashlib.sha256).hexdigest()
    return f"aurix.{b64_payload}.{signature}"

def verify_session_token(token: str) -> Dict:
    try:
        parts = token.split(".")
        if len(parts) != 3 or parts[0] != "aurix":
            raise ValueError("Malformed token")
        b64_payload, signature = parts[1], parts[2]
        expected_sig = hmac.new(SECRET_KEY.encode(), b64_payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            raise ValueError("Invalid token signature")
        payload = json.loads(base64.urlsafe_b64decode(b64_payload.encode()).decode())
        if payload.get("exp", 0) < datetime.datetime.now(datetime.timezone.utc).timestamp():
            raise ValueError("Session expired")
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )

@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    email_clean = req.email.strip().lower()
    if not email_clean:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required.")
    
    user = USER_DATABASE.get(email_clean)
    if not user:
        # Fallback for dynamic customer onboarding testing
        user = {
            "userId": f"USR-{hashlib.md5(email_clean.encode()).hexdigest()[:6].upper()}",
            "email": email_clean,
            "fullName": email_clean.split("@")[0].replace(".", " ").title(),
            "role": "EXECUTIVE",
            "tenantId": req.tenantId or "ENTERPRISE_GLOBAL",
            "passwordHash": DEFAULT_PW_HASH,
            "permissions": ["*"]
        }
    
    # Password verification
    input_hash = hashlib.sha256((req.password or "Aurix@2026").encode()).hexdigest()
    if user.get("passwordHash") and user["passwordHash"] != input_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials supplied."
        )
    
    tenant_scope = req.tenantId or user["tenantId"]
    token = create_session_token(user, tenant_scope)
    
    return LoginResponse(
        token=token,
        user=UserProfile(
            userId=user["userId"],
            email=user["email"],
            fullName=user["fullName"],
            role=user["role"],
            tenantId=tenant_scope,
            permissions=user["permissions"]
        ),
        expiresInSeconds=86400
    )

@router.get("/me", response_model=UserProfile)
async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token.")
    
    token = authorization.replace("Bearer ", "").strip()
    payload = verify_session_token(token)
    
    user_record = USER_DATABASE.get(payload["email"], {
        "userId": payload["userId"],
        "email": payload["email"],
        "fullName": payload["email"].split("@")[0].title(),
        "role": payload["role"],
        "tenantId": payload["tenantId"],
        "permissions": ["*"]
    })
    
    return UserProfile(
        userId=user_record["userId"],
        email=user_record["email"],
        fullName=user_record["fullName"],
        role=user_record["role"],
        tenantId=payload["tenantId"],
        permissions=user_record.get("permissions", ["*"])
    )