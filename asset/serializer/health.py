from common.serializers import *
from common.fields import LogicalForeignField
from ..models import *

__all__ = [
    'HealthSerializer'
]


class HealthSerializer(BulkSerializerMixin, ManageSerializer):
    """
    主机序列化器
    """

    class Meta:
        list_serializer_class = BulkListSerializer
        fields = '__all__'
        model = MonitorData

    metric = LogicalForeignField(model=Metric, allow_null=False, allow_blank=False)
    host = LogicalForeignField(model=Host, allow_null=True, allow_blank=True)

