from django.db import models
from .mapping import DiskStatusMapping, IPStatusMapping
from common.models import ManageModel
from .network import IP
from .disk import Disk


__all__ = ['Host']


class Host(ManageModel):
    """
    主机信息
    """

    class Meta:
        db_table = 'host'
        verbose_name = '主机身份信息'
        unique_together = ('name', 'project')
        ordering = ('-created_at', 'idc', 'project')

    name = models.CharField(unique=True, max_length=64, verbose_name='主机名称')
    username = models.CharField(max_length=32, verbose_name='系统用户名称')
    password = models.CharField(max_length=32, verbose_name='密码')
    ssh_port = models.IntegerField(verbose_name='ssh端口')
    type = models.SmallIntegerField(verbose_name='主机类型')
    cpu = models.SmallIntegerField(
        verbose_name='cpu核数', null=False, blank=False)
    model = models.CharField(max_length=64, verbose_name='型号')
    memory = models.IntegerField(
        verbose_name='内存', null=False, blank=False)
    os = models.CharField(max_length=24, verbose_name='系统')

    # 逻辑外键
    project = models.CharField(max_length=32, verbose_name='项目')
    idc = models.CharField(max_length=32, verbose_name='所在机房')

    def post_delete(self):
        dq = Disk.dao.get_queryset(host=self.uuid)
        Disk.dao.bulk_update_obj(dq, host=None, status=DiskStatusMapping.index('空闲'))
        iq = IP.dao.get_queryset(host=self.uuid)
        IP.dao.bulk_update_obj(iq, host=None, status=IPStatusMapping.index('空闲'), used_to_sync=False)
