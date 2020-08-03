from common.serializers import *
from ..models import *

__all__ = [
    'ProjectSerializer'
]


class ProjectSerializer(BulkSerializerMixin, ManageSerializer):
    """
    主机序列化器
    """

    class Meta:
        list_serializer_class = BulkListSerializer
        fields = '__all__'
        model = Project

