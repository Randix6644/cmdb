from rest_framework_bulk.routes import BulkRouter
from rest_framework.urlpatterns import format_suffix_patterns
from django.urls import path
# from .views import *
from .viewsets import *

# 框架注册路由
router = BulkRouter()
router.register('hosts', HostViewSet)
router.register('metrics', MetricViewSet)
router.register('disks', DiskViewSet)
router.register('health', HealthViewSet)
router.register('idc', IDCViewSet)
router.register('ip', IPViewSet)
router.register('project', ProjectViewSet)

urlpatterns = router.urls

