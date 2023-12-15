import base64
from io import BytesIO
from PIL import Image


def pil_to_base64(img, format="jpeg"):
    buffer = BytesIO()
    img.save(buffer, format)
    img_str = base64.b64encode(buffer.getvalue()).decode("ascii")

    return img_str


# 画像を読み込む。
img = Image.open("yukari_icon_min.jpg")

# base64 文字列 (jpeg) に変換する。
img_base64 = pil_to_base64(img, format="jpeg")
print(img_base64)

# base64 文字列 (png) に変換する。
# img_base64 = pil_to_base64(img, format="png")