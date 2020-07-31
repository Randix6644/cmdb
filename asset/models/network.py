from django.db import models
from .host import *
from common.models import DisplayModel
from utils.dao import QueryObjectError


class IP(DisplayModel):
    class Meta:
        db_table = 'ip'
        unique_together = (('address', 'host'),)
    address = models.CharField(db_index=True, max_length=255, verbose_name='ip地址')
    type = models.CharField(max_length=255, verbose_name='ip类型')
    bandwidth = models.IntegerField(null=True, verbose_name='带宽大小')
    status = models.CharField(max_length=100, null=True, verbose_name='状态')
    idc = models.IntegerField(null=False, blank=False, verbose_name='供应商')

    # 逻辑外键
    parent = models.CharField(index=True, max_length=255, verbose_name='宿主机IP')
    host = models.CharField(index=True, max_length=255, verbose_name='主机UUID')

    def pre_create(self, data: dict):
        parent_ip = data.get('parent')
        host = data.get('host')
        if parent_ip:
            try:
                IP.dao.get_obj(address=parent_ip)
            except QueryObjectError as e:
                raise QueryObjectError()
        if host:
            try:
                Host.dao.get_obj(uuid=host)
            except QueryObjectError as e:
                raise QueryObjectError()
