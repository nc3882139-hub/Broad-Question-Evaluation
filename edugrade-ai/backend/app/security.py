from fastapi import Depends, Header, HTTPException

from app.config import settings


def current_user(x_user_id: str | None = Header(default=None),
                 x_role: str | None = Header(default=None)):
    if not settings.AUTH_ENABLED:
        return {"id": "dev-teacher", "role": "teacher"}
    if not x_user_id or x_role not in settings.AUTH_ROLES:
        raise HTTPException(status_code=401, detail="Authentication required")
    return {"id": x_user_id[:128], "role": x_role}


def require_roles(*roles):
    def dependency(user=Depends(current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency


def owns(record, user, field="user_id"):
    return user["role"] == "admin" or getattr(record, field, None) in (None, user["id"])
