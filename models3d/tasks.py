import os, tempfile, pathlib, shutil, traceback, requests, zipfile
from celery import shared_task
from django.db import transaction
from .models import Model3D, Stage
from .pipeline.preprocess import normalize_and_save
from .pipeline.colmap import colmap_from_dir
from .pipeline.mesh import poisson_to_glb
from .pipeline.storage import upload_artifact

def _upd(obj: Model3D, stage=None, progress=None, msg=None):
    if stage: obj.stage = stage
    if progress is not None: obj.progress = progress
    if msg: obj.message = msg
    obj.save(update_fields=["stage","progress","message","updated_at"])

def _callback(obj: Model3D):
    if not obj.callback_url:
        return
    try:
        payload = {
            "id": str(obj.id),
            "stage": obj.stage,
            "point_cloud_url": obj.point_cloud_url,
            "mesh_url": obj.mesh_url,
            "title": obj.title,
        }
        requests.post(obj.callback_url, json=payload, timeout=5)
    except Exception:
        # 콜백 실패는 로그로 확인하고 흐름 차단하지 않음
        pass

@shared_task
def process_six_images_task(model_id: str):
    obj = Model3D.objects.get(pk=model_id)
    work = tempfile.mkdtemp(prefix=f"job_{obj.id}_")
    images_dir = os.path.join(work, "images")
    out_dir = os.path.join(work, "out")
    pathlib.Path(out_dir).mkdir(parents=True, exist_ok=True)

    try:
        _upd(obj, Stage.PREPROCESS, 5, "전처리(회전 보정/리사이즈)")
        normalize_and_save(obj.images, images_dir, max_side=2048)

        _upd(obj, Stage.SFM, 20, "특징 추출/매칭 및 맵 구성")
        fused_ply = colmap_from_dir(images_dir, work)  # patch_match까지 수행
        _upd(obj, Stage.FUSION, 60, "스테레오 퓨전 완료(fused.ply)")

        _upd(obj, Stage.POISSON, 70, "Poisson 재구성/클리닝/리덕션")
        mesh_path = os.path.join(out_dir, "mesh.obj")
        glb_path  = os.path.join(out_dir, "model.glb")
        poisson_to_glb(fused_ply, mesh_path, glb_path, depth=10)

        _upd(obj, Stage.UPLOAD, 85, "아티팩트 업로드")
        pcd_url = upload_artifact(fused_ply, "fused.ply")
        glb_url = upload_artifact(glb_path,  "model.glb")

        with transaction.atomic():
            obj.point_cloud_url = pcd_url
            obj.mesh_url = glb_url
            obj.stage = Stage.READY_FOR_NEXT
            obj.progress = 100
            obj.message = "3D 생성 완료"
            obj.save()

        _callback(obj)

    except Exception as e:
        traceback.print_exc()
        _upd(obj, Stage.FAILED, 0, f"오류: {e}")
    finally:
        shutil.rmtree(work, ignore_errors=True)

@shared_task
def process_model3d_task(model_id: str):
    """이미지가 미리 업로드된 모델을 실행하는 일반 태스크(가변 장수).
    프론트에서 /models/{id}/images 로 여러 장 올려두고 /models/{id}/run 으로 실행.
    """
    obj = Model3D.objects.get(pk=model_id)
    work = tempfile.mkdtemp(prefix=f"job_{obj.id}_")
    images_dir = os.path.join(work, "images")
    out_dir = os.path.join(work, "out")
    pathlib.Path(out_dir).mkdir(parents=True, exist_ok=True)

    try:
        _upd(obj, Stage.PREPROCESS, 5, "전처리(회전 보정/리사이즈)")
        normalize_and_save(obj.images, images_dir, max_side=2048)

        _upd(obj, Stage.SFM, 20, "특징 추출/매칭 및 맵 구성")
        fused_ply = colmap_from_dir(images_dir, work)
        _upd(obj, Stage.FUSION, 60, "스테레오 퓨전 완료(fused.ply)")

        _upd(obj, Stage.POISSON, 70, "Poisson 재구성/클리닝/리덕션")
        mesh_path = os.path.join(out_dir, "mesh.obj")
        glb_path  = os.path.join(out_dir, "model.glb")
        poisson_to_glb(fused_ply, mesh_path, glb_path, depth=10)

        _upd(obj, Stage.UPLOAD, 85, "아티팩트 업로드")
        pcd_url = upload_artifact(fused_ply, "fused.ply")
        glb_url = upload_artifact(glb_path,  "model.glb")

        with transaction.atomic():
            obj.point_cloud_url = pcd_url
            obj.mesh_url = glb_url
            obj.stage = Stage.READY_FOR_NEXT
            obj.progress = 100
            obj.message = "3D 생성 완료"
            obj.save()

        _callback(obj)

    except Exception as e:
        traceback.print_exc()
        _upd(obj, Stage.FAILED, 0, f"오류: {e}")
    finally:
        shutil.rmtree(work, ignore_errors=True)
