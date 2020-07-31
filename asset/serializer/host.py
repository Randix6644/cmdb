from rest_framework.serializers import CharField, IntegerField
from common.serializers import *
from common.fields import TypeIntegerField
from .. models.mapping import *
from ..models import Host


__all__ = [
    'HostSerializer'
]


class HostSerializer(BulkSerializerMixin, ManageSerializer):
    """
    账单原始序列化器
    """

    class Meta:
        list_serializer_class = BulkListSerializer
        fields = '__all__'
        model = Host
    name = CharField(
        max_length=64,
        min_length=1,
        trim_whitespace=False,
        allow_blank=False,
        allow_null=False)
    username = CharField(
        max_length=32,
        min_length=1,
        trim_whitespace=False,
        allow_blank=False,
        allow_null=False)
    password = CharField(
        max_length=64,
        min_length=1,
        trim_whitespace=False,
        allow_blank=False,
        allow_null=False)
    ssh_port = IntegerField(max_value=65536, min_value=22)
    type = TypeIntegerField(mapping=host_type, max_value=1, min_value=0)
    cpu = IntegerField(min_value=1, allow_null=False)
    cpu_model = CharField(max_length=128, allow_null=True)
    memory = IntegerField(allow_null=False)
    os = CharField(max_length=24, verbose_name='系统')
