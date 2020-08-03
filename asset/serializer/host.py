from rest_framework.serializers import IntegerField
from common.serializers import *
from common.fields import TypeIntegerField, LogicalForeignField
from ..models import *


__all__ = [
    'HostSerializer'
]


class HostSerializer(BulkSerializerMixin, ManageSerializer):
    """
    主机序列化器
    """
    class Meta:
        list_serializer_class = BulkListSerializer
        fields = '__all__'
        model = Host

    ssh_port = IntegerField(max_value=65536, min_value=22)
    type = TypeIntegerField(mapping=host_type, max_value=1, min_value=0)
    cpu = IntegerField(min_value=1, allow_null=False)
    idc = LogicalForeignField(model=IDC)
