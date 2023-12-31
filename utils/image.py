import io
import logging
from PIL import Image

__all__ = ["resize_avatar"]


def resize_avatar(image):
    try:
        im = Image.open(io.BytesIO(image))
        im = im.resize((30, 30))
        buffer = io.BytesIO() 
        im.save(buffer, format='PNG')
        img_bytes = buffer.getvalue()
        return img_bytes
    except Exception as e:
        logging.ERROR("Error resizing image: ", e)
        return None