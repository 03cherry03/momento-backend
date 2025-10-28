from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import Model3D, Model3DImage, Stage
from .serializers import (
    Model3DReadSerializer, Model3DCreateSerializer,
    Model3DImageSerializer, Model3DStatusSerializer, Model3DArtifactsSerializer
)
from .tasks import process_six_images_task, process_model3d_task

class Model3DViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    queryset = Model3D.objects.all().order_by('-created_at')

    def get_serializer_class(self):
        if self.action in ['create', 'six']:
            return Model3DCreateSerializer
        elif self.action in ['status']:
            return Model3DStatusSerializer
        elif self.action in ['artifacts']:
            return Model3DArtifactsSerializer
        return Model3DReadSerializer

    # POST /api/v1/models  (메타만 생성)
    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        with transaction.atomic():
            obj = Model3D.objects.create(
                title=ser.validated_data.get('title', ''),
                callback_url=ser.validated_data.get('callback_url', ''),
                stage=Stage.PENDING, progress=0, message="생성됨(이미지 업로드 대기)"
            )
        return Response(Model3DReadSerializer(obj).data, status=status.HTTP_201_CREATED)

    # POST /api/v1/models/six  (6장 업로드 + 실행)
    @action(detail=False, methods=['post'], url_path='six')
    def six(self, request):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        images = request.FILES.getlist('images')
        if len(images) != 6:
            return Response({"detail": "이미지는 정확히 6장을 업로드해야 합니다."},
                            status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            obj = Model3D.objects.create(
                title=ser.validated_data.get('title', ''),
                callback_url=ser.validated_data.get('callback_url', ''),
                stage=Stage.PENDING, progress=0, message="대기열 진입"
            )
            for idx, f in enumerate(images):
                Model3DImage.objects.create(model=obj, order=idx, image=f)
        process_six_images_task.delay(str(obj.id))
        return Response(Model3DReadSerializer(obj).data, status=status.HTTP_201_CREATED)

    # POST /api/v1/models/{id}/run  (사전 업로드 모델 실행)
    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        obj = self.get_object()
        process_model3d_task.delay(str(obj.id))
        return Response({"detail": "실행 시작", "id": str(obj.id)})

    # GET /api/v1/models/{id}/status
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        obj = self.get_object()
        return Response(Model3DStatusSerializer(obj).data)

    # GET /api/v1/models/{id}/artifacts
    @action(detail=True, methods=['get'])
    def artifacts(self, request, pk=None):
        obj = self.get_object()
        return Response(Model3DArtifactsSerializer(obj).data)

    # POST /api/v1/models/{id}/cancel (옵션)
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        obj = self.get_object()
        obj.stage = Stage.FAILED
        obj.message = "사용자 취소"
        obj.save(update_fields=['stage','message'])
        return Response({"detail": "취소됨"})


class Model3DImageViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = Model3DImageSerializer

    def get_queryset(self):
        return Model3DImage.objects.filter(model_id=self.kwargs['model_pk']).order_by('order')

    def create(self, request, model_pk=None):
        model = get_object_or_404(Model3D, pk=model_pk)
        file = request.FILES.get('image')
        order = int(request.data.get('order', 0))
        img = Model3DImage.objects.create(model=model, order=order, image=file)
        return Response(Model3DImageSerializer(img).data, status=status.HTTP_201_CREATED)
