import os
from django.conf import settings

def upload_artifact(local_path: str, key_hint: str) -> str:
    """S3 사용 시 퍼블릭 URL 반환, 아니면 로컬 MEDIA/artifacts 경로에 복사 후 URL 반환.
    운영 환경에서는 권한/보안 정책에 맞춰 ACL을 적절히 설정하세요.
    """
    if getattr(settings, "USE_S3", False):
        import boto3, uuid
        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )
        key = f"artifacts/{uuid.uuid4().hex}_{os.path.basename(key_hint)}"
        s3.upload_file(local_path, settings.AWS_S3_BUCKET, key, ExtraArgs={"ACL": "public-read"})
        return f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{key}"
    else:
        media_dir = settings.MEDIA_ROOT / "artifacts"
        os.makedirs(media_dir, exist_ok=True)
        dst = media_dir / os.path.basename(key_hint)
        with open(local_path, "rb") as src, open(dst, "wb") as out:
            out.write(src.read())
        return f"{settings.MEDIA_URL}artifacts/{os.path.basename(dst)}"
