from django.db import models
from .host import Host
from .network import IP
from .disk import Disk
from common.models import ManageModel
from utils import DeleteObjectError

__all__ = ['IDC']


class IDC(ManageModel):
    class Meta:
        db_table = 'idc'
        ordering = ('-name', )
    name = models.CharField(unique=True, max_length=64, verbose_name='idc名称')
    region = models.CharField(db_index=True, max_length=64, verbose_name='地区')
    is_enabled = models.BooleanField(default=True, verbose_name="是否激活")

    def pre_delete(self):
        host = Host.dao.get_queryset(idc=self.uuid)
        disk = Disk.dao.get_queryset(idc=self.uuid)
        ip = IP.dao.get_queryset(idc=self.uuid)
        if not all([host, disk, ip]):
            raise DeleteObjectError(f'IDC: {self.uuid} linked to multiple resources, unbind before deleting')
