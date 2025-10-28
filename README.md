# Momento 3D Backend (Django + DRF + Celery)

스마트폰으로 촬영한 사진 **6장**을 업로드하면 서버에서 **SFM/MVS(COLMAP)** → **Poisson 재구성(Open3D)** → **GLB 내보내기(Trimesh)**까지 자동으로 처리하고, 결과 아티팩트를 URL로 제공합니다. 프런트는 React Native를 가정합니다.

## 주요 기능
- **사진 6장 업로드 + 즉시 실행**: `/api/v1/models/six`
- **SFM/MVS → fused.ply → Poisson → GLB** 전체 파이프라인
- **진행률/단계** 업데이트: `stage`, `progress`, `message`
- **콜백 URL**(옵션): 완료 시 외부 서비스로 결과 POST
- **S3 업로드(선택)** 또는 로컬 `MEDIA` 저장

## 스택
- Backend: Django 4 + DRF, Celery
- Worker: Celery + Redis (broker/result)
- 3D: COLMAP (바이너리 필요), Open3D, Trimesh, Pillow
- Storage: AWS S3(옵션) 또는 로컬

## 설치
```bash
git clone <this-repo>
cd momento-backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 환경값 수정
python manage.py migrate
python manage.py runserver
