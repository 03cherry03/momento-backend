import uuid
from django.db import models

class Stage(models.TextChoices):
    PENDING = "PENDING"
    PREPROCESS = "PREPROCESS"
    SFM = "SFM"
    MVS = "MVS"
    FUSION = "FUSION"
    POISSON = "POISSON"
    EXPORT = "EXPORT"
    UPLOAD = "UPLOAD"
    READY_FOR_NEXT = "READY_FOR_NEXT"
    FAILED = "FAILED"

class Model3D(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, blank=True)
    stage = models.CharField(max_length=20, choices=Stage.choices, default=Stage.PENDING)
    progress = models.PositiveSmallIntegerField(default=0)
    message = models.TextField(blank=True)
    callback_url = models.URLField(blank=True)

    point_cloud_url = models.URLField(blank=True)  # fused.ply
    mesh_url = models.URLField(blank=True)         # model.glb

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Model3DImage(models.Model):
    model = models.ForeignKey(Model3D, on_delete=models.CASCADE, related_name="images")
    order = models.PositiveSmallIntegerField()  # 0..N
    image = models.ImageField(upload_to="uploads/")

    class Meta:
        ordering = ["order"]
