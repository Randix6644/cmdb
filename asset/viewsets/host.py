from common.viewsets import BulkManageViewSet
from ..models import Host
from ..serializer import HostSerializer


__all__ = [
    'HostViewSet'
]


class HostAbstractViewSet(BulkManageViewSet):
    @staticmethod
    def perform_create(serializer):
        """
        执行创建
        """
        serializer.create_relative_models()

    @staticmethod
    def perform_update(serializer):
        """
        执行更新
        """
        serializer.update_relative_models()


class HostViewSet(HostAbstractViewSet):
    """
    项目视图集
    """
    queryset = Host.objects.all()
    serializer_class = HostSerializer
    lookup_field = 'uuid'
