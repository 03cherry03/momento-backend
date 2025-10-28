from rest_framework import serializers
from .models import Model3D, Model3DImage

class Model3DCreateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True)
    callback_url = serializers.URLField(required=False, allow_blank=True)
    images = serializers.ListField(child=serializers.ImageField(), required=False)

class Model3DReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Model3D
        fields = ("id","title","stage","progress","message",
                  "point_cloud_url","mesh_url","created_at")

class Model3DStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Model3D
        fields = ("id","stage","progress","message")

class Model3DArtifactsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Model3D
        fields = ("id","point_cloud_url","mesh_url")

class Model3DImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Model3DImage
        fields = ("id","order","image")
