import io
import os
import re
from PIL import Image
from django.core.files.base import ContentFile
from common.exceptions import BusinessException


def normalize_phone_number(phone: str) -> str:
    """نرمال‌سازی شماره موبایل به فرمت استاندارد 09XXXXXXXXX"""
    phone = str(phone).strip().replace(" ", "").replace("-", "")
    if phone.startswith("+98"):
        phone = "0" + phone[3:]
    elif phone.startswith("98"):
        phone = "0" + phone[2:]
    elif phone.startswith("9") and len(phone) == 10:
        phone = "0" + phone

    if not re.match(r"^09\d{9}$", phone):
        raise BusinessException("شماره موبایل وارد شده معتبر نیست.", code="INVALID_PHONE_NUMBER")
    return phone


def compress_image_to_webp(image_field, max_width: int = 1200, quality: int = 82) -> ContentFile:
    """تبدیل خودکار تصاویر آپلود شده به فرمت WebP و بهینه‌سازی ابعاد"""
    img = Image.open(image_field)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")

    if img.width > max_width:
        ratio = max_width / float(img.width)
        new_height = int((float(img.height) * float(ratio)))
        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

    output = io.BytesIO()
    img.save(output, format="WEBP", quality=quality, optimize=True)
    output.seek(0)

    base_name = os.path.splitext(os.path.basename(image_field.name))[0]
    return ContentFile(output.read(), name=f"{base_name}.webp")