from common.viewsets import BulkManageViewSet
from ..models import IP
from ..serializer import IPSerializer


__all__ = [
    'IPViewSet'
]


class IPViewSet(BulkManageViewSet):
    """
    项目视图集
    """
    queryset = IP.objects.all()
    serializer_class = IPSerializer
    lookup_field = 'uuid'
