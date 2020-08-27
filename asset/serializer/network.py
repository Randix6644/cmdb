from rest_framework.serializers import IntegerField, IPAddressField, BooleanField
from common.serializers import *
from common.fields import TypeIntegerField, LogicalForeignField
from ..models import *

__all__ = ['IPSerializer']


class IPSerializer(BulkSerializerMixin, ManageSerializer):
    class Meta:
        list_serializer_class = BulkListSerializer
        # fields = '__all__'
        exclude = ('idc',)
        model = IP
    address = IPAddressField(allow_null=False)
    type = TypeIntegerField(mapping=IP_type)
    bandwidth = IntegerField(allow_null=True)
    status = TypeIntegerField(mapping=IP_status, allow_null=True)

    # 逻辑外键
    parent = LogicalForeignField(model=IP, allow_null=True, allow_blank=True)
    host = LogicalForeignField(model=Host, exclude_fields=['password'], allow_blank=True, allow_null=True)
