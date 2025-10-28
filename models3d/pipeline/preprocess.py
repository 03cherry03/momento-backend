import os, pathlib
from PIL import Image, ImageOps

def normalize_and_save(images_qs, out_dir: str, max_side: int = 2048):
    """이미지 EXIF 회전 보정, 리사이즈 후 000.jpg부터 저장.
    3D 재구성 품질을 위해 과도한 리사이즈는 피하고, 입력 순서를 고정합니다.
    """
    pathlib.Path(out_dir).mkdir(parents=True, exist_ok=True)
    for img in images_qs.order_by("order"):
        with Image.open(img.image.path) as im:
            im = ImageOps.exif_transpose(im)  # 회전 보정
            im.thumbnail((max_side, max_side))
            out_path = os.path.join(out_dir, f"{img.order:03d}.jpg")
            im.save(out_path, quality=92)
