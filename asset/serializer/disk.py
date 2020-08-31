from common.serializers import *
from common.fields import TypeIntegerField, LogicalForeignField
from ..models import *

__all__ = [
    'DiskSerializer'
]


class DiskSerializer(BulkSerializerMixin, ManageSerializer):
    """
    主机序列化器
    """

    class Meta:
        list_serializer_class = BulkListSerializer
        fields = '__all__'
        model = Disk

    # type = TypeIntegerField(mapping=disk_type, allow_null=False)
    status = TypeIntegerField(mapping=DiskStatusMapping, allow_null=False)
    idc = LogicalForeignField(model=IDC, allow_null=False, allow_blank=False)
    host = LogicalForeignField(
        model=Host,
        exclude_fields=['password'],
        allow_null=True,
        allow_blank=True)
