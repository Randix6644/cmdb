from common.serializers import *
from common.fields import TypeIntegerField
from ..models import *

__all__ = [
    'MetricSerializer'
]


class MetricSerializer(BulkSerializerMixin, ManageSerializer):
    """
    主机序列化器
    """

    class Meta:
        list_serializer_class = BulkListSerializer
        fields = '__all__'
        model = Metric

    type = TypeIntegerField(mapping=MetricTypeMapping)

