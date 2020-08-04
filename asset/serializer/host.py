from rest_framework.serializers import IntegerField, IPAddressField
from common.serializers import *
from common.fields import TypeIntegerField, LogicalForeignField
from controller import *
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
    cpu = IntegerField(min_value=1, allow_null=False, required=False)
    idc = LogicalForeignField(model=IDC, required=True)
    ip = IPAddressField(write_only=True, required=True)

    def save(self, **kwargs):
        self.validated_data.pop('ip')
        ip = kwargs.pop('ip')
        super().save(**kwargs)

    def initialize_host(self, **kwargs):
        init = cfg.get('ansible', 'init_pb')
        facts = cfg.get('ansible', 'fact_pb')
        user = self.validated_data.get('username')
        password = self.validated_data.get('password')
        ip = self.validated_data.pop('ip')
        ssh_port = self.validated_data.get('ssh_port', 22)
        addr = f"{ip}:{str(ssh_port)}"
        extra_vars = {"user": user, "password": password, "server": addr}
        rst = LinuxCollectorFactory().exec([addr], [init, facts], extra_vars, user=user)
