from common.viewsets import BulkManageViewSet
from ..models import IDC
from ..serializer import IDCSerializer


__all__ = [
    'IDCViewSet'
]


class IDCViewSet(BulkManageViewSet):
    """
    项目视图集
    """
    queryset = IDC.objects.all()
    serializer_class = IDCSerializer
    lookup_field = 'uuid'
    search_fields = ('name',)
