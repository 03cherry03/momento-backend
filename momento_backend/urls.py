from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from models3d.views import Model3DViewSet, Model3DImageViewSet

router = DefaultRouter()
router.register(r'models', Model3DViewSet, basename='models')

nested = NestedDefaultRouter(router, r'models', lookup='model')
nested.register(r'images', Model3DImageViewSet, basename='model-images')

urlpatterns = [
    path(settings.API_PREFIX.strip('/') + '/', include(router.urls)),
    path(settings.API_PREFIX.strip('/') + '/', include(nested.urls)),

    # OpenAPI & Swagger
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
