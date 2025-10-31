from fastapi import APIRouter, Depends, Request
from .auth_service import verify_token
import firebase_admin
from firebase_admin import auth
from fastapi import Request, HTTPException

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/verify")
def verify_user(request: Request):
    decoded = verify_token(request)
    return {"message": "Token valid", "user": decoded}


@router.get("/test-public")
def test_public():
    """Public endpoint - no auth needed (for testing)"""
    return {"message": "Public endpoint works!"}


@router.get("/test-protected")
def test_protected(request: Request):
    """Protected endpoint - requires valid Firebase token (for testing)"""
    decoded = verify_token(request)
    return {
        "message": "Protected endpoint works!",
        "user_id": decoded.get("uid"),
        "email": decoded.get("email"),
    }


@router.get("/test")
def test_firebase():
    try:
        try:
            app = firebase_admin.get_app()
        except ValueError:
            cred = firebase_admin.credentials.Certificate(
                "authentication/firebase-adminsdk.json"
            )
            app = firebase_admin.initialize_app(cred)

        return {
            "message": "Firebase connected successfully ✅",
            "project_id": app.project_id,
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/verify")
async def verify_token(request: Request):
    try:
        data = await request.json()
        id_token = data.get("idToken")

        if not id_token:
            raise HTTPException(status_code=400, detail="Missing ID token")

        # Verify Firebase token
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token.get("uid")
        email = decoded_token.get("email")

        return {
            "message": "Token verified successfully ✅",
            "uid": uid,
            "email": email,
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
