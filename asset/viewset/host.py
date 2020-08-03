from common.viewsets import BulkManageViewSet
from ..models import Host
from ..serializer import HostSerializer


__all__ = [
    'HostViewSet'
]


class HostViewSet(BulkManageViewSet):
    """
    项目视图集
    """
    queryset = Host.objects.all()
    serializer_class = HostSerializer
    lookup_field = 'uuid'
