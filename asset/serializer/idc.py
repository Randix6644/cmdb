from common.serializers import *
from ..models import *

__all__ = [
    'IDCSerializer'
]


class IDCSerializer(BulkSerializerMixin, ManageSerializer):
    """
    主机序列化器
    """

    class Meta:
        list_serializer_class = BulkListSerializer
        fields = '__all__'
        model = IDC

