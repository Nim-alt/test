from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from defects.views import DefectViewSet

router = DefaultRouter()
router.register(r'defects', DefectViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),      # 所有 API 都放在 /api/ 下面
]