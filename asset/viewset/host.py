from common.viewsets import BulkManageViewSet
from ..models import Host
# from ..serializers import DomainSerializer


__all__ = [
    'DomainViewSet'
]


class DomainViewSet(BulkManageViewSet):
    """
    项目视图集
    """
    queryset = Host.objects.all()
    serializer_class = DomainSerializer
    lookup_field = 'uuid'
