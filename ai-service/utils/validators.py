import os
import secrets
import re
from fastapi import Header, HTTPException

def require_gateway(x_service_key: str = Header(default='')):
    expected = os.getenv('AI_SERVICE_SECRET', '')
    if len(expected) < 32:
        raise HTTPException(503, 'AI_SERVICE_SECRET must contain at least 32 characters')
    if not secrets.compare_digest(x_service_key, expected):
        raise HTTPException(401, 'Authorized backend access required')

def require_user(x_user_id: str = Header(default='')) -> str:
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', x_user_id):
        raise HTTPException(401, 'Authenticated user context required')
    return x_user_id
