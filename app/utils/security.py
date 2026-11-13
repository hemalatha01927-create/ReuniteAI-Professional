import os
import uuid
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename
from flask import current_app, abort


def save_private_image(file_storage):
    """Validate and re-encode an uploaded image, removing EXIF metadata."""
    if not file_storage or not file_storage.filename:
        return None
    if not current_app.config["UPLOADS_ENABLED"]:
        raise ValueError("Photo uploads are temporarily disabled on this public preview.")
    original = secure_filename(file_storage.filename)
    ext = original.rsplit(".", 1)[-1].lower() if "." in original else ""
    if ext not in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        raise ValueError("Use a JPG, JPEG, PNG or WEBP image.")
    try:
        image = Image.open(file_storage.stream)
        image.verify()
        file_storage.stream.seek(0)
        image = Image.open(file_storage.stream).convert("RGB")
        image.thumbnail((1800, 1800))
    except (UnidentifiedImageError, OSError, ValueError):
        raise ValueError("The uploaded file is not a valid image.")
    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    filename = f"{uuid.uuid4().hex}.jpg"
    image.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename), "JPEG", quality=88, optimize=True)
    return filename


def private_image_path(filename):
    if not filename or os.path.basename(filename) != filename:
        abort(404)
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    if not os.path.isfile(path):
        abort(404)
    return path
