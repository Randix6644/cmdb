from rest_framework.serializers import *
from utils import generate_unique_uuid, hash_string, logger
from typing import List
from common.serializers import *
from common.fields import *
from utils import CreateObjectError
from monitor import *
from . import *
from ..models import *
from cmdb.configs import *


__all__ = [
    'HostSerializer'
]


class MemorySerializer(IntegerField):
    def to_representation(self, value):
        value = f'{round(super().to_representation(value)/1024, 2)} G'
        return value


class HostSerializer(BulkSerializerMixin, ManageSerializer):
    """
    主机序列化器
    """
    class Meta:
        list_serializer_class = BulkListSerializer
        fields = '__all__'
        model = Host

    ssh_port = IntegerField(max_value=65536, min_value=22)
    type = TypeIntegerField(mapping=HostTypeMapping, min_value=0)
    username = CharField(max_length=64)
    password = CharField(max_length=63, write_only=True)

    # read_only
    os = CharField(read_only=True)
    model = CharField(read_only=True)
    cpu = IntegerField(read_only=True)
    memory = MemorySerializer(read_only=True)

    # read_only and foreign models
    ips = SerializerMethodField()
    disks = SerializerMethodField()

    # write only and pop
    ip = IPAddressField(write_only=True)
    parent_ip = IPAddressField(write_only=True, required=False)
    bandwidth = IntegerField(write_only=True, required=False)

    # 逻辑外键
    idc = LogicalForeignField(model=IDC)
    project = LogicalForeignField(model=Project)

    @staticmethod
    def get_ips(obj):
        host_uuid = obj.uuid
        ins = IP.dao.get_queryset(host=host_uuid)
        serializer = IPSerializer(
            ins,
            standalone=True,
            exclude_fields=(
                'created_at',
                'id',
                'created_by',
                'updated_by'),
            many=True)
        return serializer.data

    @staticmethod
    def get_disks(obj):
        host_uuid = obj.uuid
        disk_ids = DiskHost.dao.get_field_value('disk_id', host_id=host_uuid)
        ins = Disk.dao.get_queryset().filter(uuid__in=disk_ids)
        serializer = DiskSerializer(
            ins,
            standalone=True,
            exclude_fields=(
                'created_at',
                'id',
                'created_by',
                'updated_by'),
            many=True)
        return serializer.data

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
            raise Exception(
                'invalid param, ip, parent_ip, and bandwidth are not allowed to be modified by this api.')
        super().save(**kwargs)

    def _gather_host_info(self):
        init = CFG.get('ansible', 'init_pb')
        facts = CFG.get('ansible', 'fact_pb')
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
        print(extra_vars)
        linux_collector_factory_run_with_process([addr], [init], 'host initialization', extra_vars, user=user)
        host_info = linux_collector_factory_run_with_process([addr], [facts], 'host data collection',
                                                             extra_vars, user=user)
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
        ip_set = sorted(set(ip_set), key=ip_set.index)
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
                'status': IPStatusMapping.index('已绑定'),
                'parent': parent,
                'host': host
            })
        # 用户输入的ip 最后append进来的， 用来作同步用
        ip_kwargs[-1]['used_to_sync'] = True
        return ip_kwargs

    @staticmethod
    def parse_disk_info(idc: str, host: str, disk_info: dict) -> List[dict]:
        disks = []
        logger.debug(f"Parsing disk info, disk_info:{disk_info}")
        disk_keys = [k for k in disk_info if k.startswith(
            "vd") or k.startswith('sd')]
        for k in disk_keys:
            ids = ''.join(disk_info.get(k)['links']['ids'])
            ids = str(ids)
            p = disk_info[k].get('partitions')
            for part, v in p.items():
                uid = str(v.get('uuid'))
                ids = uid + ids
            uuid = hash_string(ids)
            if not uuid:
                continue
            # 先不做单位转换
            size = int(float(disk_info[k]['size'].split()[0]))
            create_kwargs = {
                'uuid': uuid,
                'partition': k,
                'size': size,
                'idc': idc,
                'host': host}
            disks.append(create_kwargs)
        return disks

    @staticmethod
    def create_disks(disk_set: List[dict]):
        logger.debug(f'creating disks: {disk_set}')
        # Disk.dao.bulk_create_obj(disk_set)
        for d in disk_set:
            host_uuid = d.pop('host')
            disk_uuid = d.get('uuid')
            # 一个磁盘可能被多台机器使用，lvm
            disk_obj = Disk.dao.get_queryset(uuid=disk_uuid, empty=True)
            if not disk_obj:
                Disk.dao.create_obj(**d)
            DiskHost.dao.create_obj(host_id=host_uuid, disk_id=disk_uuid)

    @staticmethod
    def create_ips(ip_set: List[dict]):
        # 拿最后一个元素出来， 即本次创建主机用来同步的ip
        synced_ip_kwargs = ip_set[-1]
        sync_ip = IP.dao.get_queryset(address=synced_ip_kwargs.get('address'), type=IPTypeMapping.index('外网'), empty=True)
        # 查看此ip 是否以前存在解绑过的， 修改状态和标识即可。 如果是内网网址，通过定时任务删除， 内网不存在解绑，只可能是变更Ip.
        # 即再同步任务时序检查内网ip是否变更，入变更需将原来的内网IP删掉。（还没写）
        if sync_ip:
            IP.dao.update_obj(sync_ip[0], used_to_sync=True, status=IPStatusMapping.index('已绑定'), host=synced_ip_kwargs.get('host'))
            ip_set.pop()
        logger.debug(f'creating ips: {ip_set}')
        IP.dao.bulk_create_obj(ip_set)
