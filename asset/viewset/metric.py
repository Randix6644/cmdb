from common.viewsets import BulkManageViewSet
from ..models import Metric
from ..serializer import MetricSerializer


__all__ = [
    'MetricViewSet'
]


class MetricViewSet(BulkManageViewSet):
    """
    项目视图集
    """
    queryset = Metric.objects.all()
    serializer_class = MetricSerializer
    lookup_field = 'uuid'
