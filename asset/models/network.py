from django.db import models
import ipaddress
from .host import *
from common.models import ManageModel
from .mapping import IP_type
from utils.dao import QueryObjectError

__all__ = ['IP']


class IP(ManageModel):
    class Meta:
        db_table = 'ip'
        unique_together = (('address', 'host'),)
    address = models.CharField(db_index=True, max_length=255, verbose_name='ip地址')
    type = models.CharField(max_length=255, verbose_name='ip类型')
    bandwidth = models.IntegerField(null=True, verbose_name='带宽大小')
    status = models.SmallIntegerField(blank=True, null=True, verbose_name='状态')

    # 逻辑外键
    idc = models.CharField(max_length=32, null=False, blank=False, verbose_name='供应商')
    parent = models.CharField(max_length=32, verbose_name='宿主机IP', null=True, blank=True)
    host = models.CharField(db_index=True, null=True, blank=True, max_length=255, verbose_name='主机UUID')

    @classmethod
    def pre_create(cls, data: dict):
        addr = data.get('address')
        if ipaddress.ip_address(addr).is_private:
            data['type'] = IP_type.index('内网')
        else:
            data['type'] = IP_type.index('外网')
            if IP.dao.get_queryset(address=addr, empty=True):
                raise Exception(f'ip already exist{addr}')
        super().pre_create(data)
