from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from firebase_admin import storage
import uuid

from app.dependencies.auth import get_current_user
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


class UpdateProfileDTO(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[str] = None


@router.put("/profile")
def update_profile(
    body: UpdateProfileDTO,
    user=Depends(get_current_user),
):
    return user_service.update_profile(
        uid=user["uid"],
        first_name=body.firstName,
        last_name=body.lastName,
        email=body.email,
    )


@router.post("/profile/photo")
async def update_profile_photo(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png", "webp"]:
        raise HTTPException(
            status_code=422,
            detail="Only jpg, png, webp allowed"
        )

    bucket = storage.bucket()
    blob_name = f"avatars/{user['uid']}/{uuid.uuid4()}.{ext}"
    blob = bucket.blob(blob_name)
    contents = await file.read()
    blob.upload_from_string(contents, content_type=file.content_type)

    encoded = blob_name.replace("/", "%2F")
    photo_url = f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/{encoded}?alt=media"

    return user_service.update_profile_photo(user["uid"], photo_url)