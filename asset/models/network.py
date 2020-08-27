from django.db import models
import ipaddress
from common.models import ManageModel
from utils.dao import CreateObjectError
from .mapping import IP_type

__all__ = ['IP']


class IP(ManageModel):
    class Meta:
        db_table = 'ip'
        unique_together = ('address', 'host')
    address = models.CharField(
        db_index=True,
        max_length=255,
        verbose_name='ip地址')
    type = models.CharField(max_length=255, verbose_name='ip类型')
    bandwidth = models.IntegerField(null=True, verbose_name='带宽大小')
    status = models.SmallIntegerField(blank=True, null=True, verbose_name='状态')
    used_to_sync = models.BooleanField(blank=True, null=True, default=False)

    # 逻辑外键
    idc = models.CharField(
        max_length=32,
        null=False,
        blank=False,
        verbose_name='供应商')
    parent = models.CharField(
        max_length=32,
        verbose_name='宿主机IP',
        null=True,
        blank=True)
    host = models.CharField(
        db_index=True,
        null=True,
        blank=True,
        max_length=255,
        verbose_name='主机UUID')

    @classmethod
    def pre_create(cls, data: dict):
        addr = data.get('address')
        if ipaddress.ip_address(addr).is_private:
            data['type'] = IP_type.index('内网')
        else:
            data['type'] = IP_type.index('外网')
            if IP.dao.get_queryset(address=addr, empty=True):
                raise Exception(f'ip already exist{addr}')
        used_to_sync = data.get('used_to_sync')
        if used_to_sync:
            r = IP.dao.get_queryset(used_to_sync=True, host=data.get('host')).values()
            if r:
                raise CreateObjectError('Only one ip can be used to sync monitor data')
        super().pre_create(data)
