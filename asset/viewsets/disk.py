from common.viewsets import BulkManageViewSet
from ..models import Disk
from ..serializer import DiskSerializer


__all__ = [
    'DiskViewSet'
]


class DiskViewSet(BulkManageViewSet):
    """
    项目视图集
    """
    queryset = Disk.objects.all()
    serializer_class = DiskSerializer
    lookup_field = 'uuid'
