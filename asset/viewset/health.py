from common.viewsets import BulkManageViewSet
from ..models import MonitorData
from ..serializer import HealthSerializer


__all__ = [
    'HealthViewSet'
]


class HealthViewSet(BulkManageViewSet):
    """
    项目视图集
    """
    queryset = MonitorData.objects.all()
    serializer_class = HealthSerializer
    lookup_field = 'uuid'
