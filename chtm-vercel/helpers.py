import os
from functools import wraps

import cloudinary
import cloudinary.uploader
from flask import session, redirect, url_for

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME", ""),
    api_key=os.environ.get("CLOUDINARY_API_KEY", ""),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET", ""),
    secure=True,
)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


class ImageUploadError(Exception):
    pass


def upload_image(file_storage, folder):
    """Uploads a werkzeug FileStorage to Cloudinary. Returns the secure URL, or None if no file was given."""
    if not file_storage or not file_storage.filename:
        return None

    if file_storage.mimetype not in ALLOWED_CONTENT_TYPES:
        raise ImageUploadError("Only JPG, PNG, WEBP, or GIF images are allowed.")

    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size > MAX_IMAGE_BYTES:
        raise ImageUploadError("Image must be smaller than 5MB.")

    try:
        result = cloudinary.uploader.upload(file_storage, folder=folder)
    except Exception as e:
        raise ImageUploadError("Failed to upload image. Please try again.") from e

    return result.get("secure_url")


def delete_image(image_url):
    """Best-effort delete of a Cloudinary image given its stored URL. Never raises."""
    if not image_url:
        return
    try:
        parts = image_url.split("/upload/")
        if len(parts) != 2:
            return
        after = parts[1]
        segments = after.split("/")
        if segments and segments[0].startswith("v") and segments[0][1:].isdigit():
            segments = segments[1:]
        public_id = "/".join(segments)
        public_id = os.path.splitext(public_id)[0]
        cloudinary.uploader.destroy(public_id)
    except Exception:
        pass


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped
