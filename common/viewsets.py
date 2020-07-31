from rest_framework.viewsets import GenericViewSet
from .mixins import *


__all__ = [
    'ManageViewSet',
    'BulkManageViewSet',
    'ReadOnlyViewSet'
]


class ManageViewSet(ListModelMixin,
                    RetrieveModelMixin,
                    CreateModelMixin,
                    UpdateModelMixin,
                    DestroyModelMixin,
                    GenericViewSet):
    """
    处理仅单个管理请求的视图集
    """
    pass


class BulkManageViewSet(ListModelMixin,
                        BulkCreateModelMixin,
                        BulkUpdateModelMixin,
                        BulkDestroyModelMixin,
                        RetrieveModelMixin,
                        UpdateModelMixin,
                        DestroyModelMixin,
                        GenericViewSet):
    """
    处理支持批量管理请求的视图集
    """
    pass


class ReadOnlyViewSet(ListModelMixin,
                      RetrieveModelMixin,
                      GenericViewSet):
    """
    处理只读请求的视图集
    """
    pass
