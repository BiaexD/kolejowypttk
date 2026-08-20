import os

from PIL import Image, ImageOps


def resize_and_compress(field_file, max_dim=1920, quality=82):
    """Downscale an uploaded image to max_dim on its longest edge and
    re-save it as a compressed JPEG, in place, to keep uploads small."""
    path = field_file.path
    with Image.open(path) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")

        width, height = img.size
        if max(width, height) > max_dim:
            ratio = max_dim / float(max(width, height))
            img = img.resize((round(width * ratio), round(height * ratio)), Image.LANCZOS)

        new_path = os.path.splitext(path)[0] + ".jpg"
        img.save(new_path, format="JPEG", quality=quality, optimize=True)

    if new_path != path:
        os.remove(path)
        field_file.name = os.path.splitext(field_file.name)[0] + ".jpg"
