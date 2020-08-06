from rest_framework.serializers import IntegerField, IPAddressField, CharField
from utils import generate_unique_uuid, hash_string
from typing import List
from common.serializers import *
from common.fields import TypeIntegerField, LogicalForeignField
from controller import *
from ..models import IP, host_type, IDC, Disk, Host, Project, IP_status
from cmdb.configs import *


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
    type = TypeIntegerField(mapping=host_type, min_value=0)
    username = CharField(max_length=64)
    password = CharField(max_length=63, write_only=True)

    # read_only
    os = CharField(read_only=True)
    model = CharField(read_only=True)
    cpu = IntegerField(read_only=True)
    memory = IntegerField(read_only=True)

    # write only and pop
    ip = IPAddressField(write_only=True)
    parent_ip = IPAddressField(write_only=True, required=False)
    bandwidth = IntegerField(write_only=True, required=False)

    # 逻辑外键
    idc = LogicalForeignField(model=IDC)
    project = LogicalForeignField(model=Project)

    def create_relative_models(self, **kwargs):
        creation_kwargs = self.get_creation_kwargs()
        super().save(**kwargs)
        disk_set = creation_kwargs.get('disk')
        ip_set = creation_kwargs.get('ip')
        self.create_disks(disk_set)
        self.create_ips(ip_set)

    def update_relative_models(self, **kwargs):
        ip = self.validated_data.pop('ip', None)
        parent_ip = self.validated_data.pop('parent_ip', None)
        bandwidth = self.validated_data.pop('bandwidth', None)
        password = self.validated_data.get('password')
        user = self.validated_data.get('user')
        ssh_port = self.validated_data.get('ssh_port')
        if password:
            if not all([ip, user, ssh_port]):
                raise Exception(
                    'ip, username, ssh_port are required to change the password')
            # 改密码重新跑一次ssh-copy-id 以防用户第一次密码输错导致后面无法远端执行。
            self._gather_host_info()
        elif any([ip, parent_ip, bandwidth]):
            raise Exception('invalid param, ip, parent_ip, and bandwidth are not allowed to be modified by this api.')
        super().save(**kwargs)

    def _gather_host_info(self):
        init = cfg.get('ansible', 'init_pb')
        facts = cfg.get('ansible', 'fact_pb')
        user = self.validated_data.get('username')
        password = self.validated_data.get('password')
        ip = self.validated_data.get('ip')
        ssh_port = self.validated_data.get('ssh_port', 22)
        addr = f"{ip}:{str(ssh_port)}"
        extra_vars = {
            "user": user,
            "password": password,
            "server": ip,
            "sshport": ssh_port}
        try:
            _ = LinuxCollectorFactory().exec(
                [addr], [init], extra_vars, user=user)
        except Exception as e:
            raise Exception(f"unable to initialize host, err{e}")
        try:
            host_info = LinuxCollectorFactory().exec(
                [addr], [facts], extra_vars, user=user)
        except Exception as e:
            raise Exception(f"unable to collect host data, err{e}")
        return host_info

    def get_creation_kwargs(self):
        host_info = self._gather_host_info()
        ip = self.validated_data.pop('ip')
        bandwidth = self.validated_data.pop('bandwidth', None)
        parent_ip = self.validated_data.pop('parent_ip', None)
        idc = self.validated_data.get('idc')
        # 自己生成， 磁盘和ip表需要用到这个id, 因为有一个有错误全部都会回滚， 不需要例会顺序。
        host_uuid = generate_unique_uuid()
        cpu = host_info['success'][ip]['cores']
        ip_set = host_info['success'][ip]['ip']
        ip_set.append(ip)
        model = str(host_info['success'][ip]['cpu'][2])
        mem = host_info['success'][ip]['ram']
        hard_disk_set = host_info['success'][ip]['disk']
        os = host_info['success'][ip]['release']
        self.fill_up_validated_data(host_uuid, cpu, mem, model, os)
        disk_kwargs = self.parse_disk_info(idc, host_uuid, hard_disk_set)
        ip_kwargs = self.create_ip_kwargs(
            bandwidth, parent_ip, host_uuid, ip_set)
        return {'disk': disk_kwargs, 'ip': ip_kwargs}

    def fill_up_validated_data(self, uuid, cpu, memory, model, os):
        fields = {
            'uuid': uuid,
            'cpu': cpu,
            'memory': memory,
            'model': model,
            'os': os}
        for f in fields:
            self.validated_data[f] = fields[f]

    @staticmethod
    def create_ip_kwargs(
            bandwidth,
            parent,
            host,
            ip_set: List) -> List[dict]:
        ip_kwargs: List[dict] = []
        for ip in ip_set:
            ip_kwargs.append({
                'address': ip,
                'bandwidth': bandwidth,
                'status': IP_status.index('已绑定'),
                'parent': parent,
                'host': host,
            })
        return ip_kwargs

    @staticmethod
    def parse_disk_info(idc: str, host: str, disk_info: dict) -> List[dict]:
        disks = []
        disk_keys = [k for k in disk_info if k.startswith(
            "vd") or k.startswith('sd')]
        for k in disk_keys:
            # uuid = disk_info[k]['links']['uuids'][0].replace('-', '')
            ids = ''.join(disk_info[k]['links']['ids'])
            uuid = hash_string(ids)
            if not uuid:
                continue
            # 先不做单位转换
            size = int(float(disk_info[k]['size'].split()[0]))
            create_kwargs = {
                'uuid': uuid,
                'size': size,
                'idc': idc,
                'host': host}
            disks.append(create_kwargs)
        return disks

    @staticmethod
    def create_disks(disk_set: List[dict]):
        Disk.dao.bulk_create_obj(disk_set)

    @staticmethod
    def create_ips(ip_set: List[dict]):
        IP.dao.bulk_create_obj(ip_set)
