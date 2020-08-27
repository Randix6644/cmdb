from django.db import models
from .mapping import disk_status
from common.models import DisplayModel


class Disk(DisplayModel):
    class Meta:
        db_table = 'disk'

    partition = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        verbose_name='盘标识')
    # type = modelsbak.SmallIntegerField(null=False, blank=False, verbose_name='类型')
    size = models.IntegerField(null=False, blank=False, verbose_name='硬盘大小')
    status = models.SmallIntegerField(
        null=False,
        blank=False,
        default=disk_status.index('挂载'),
        verbose_name='状态')

    # 逻辑外键
    idc = models.CharField(
        db_index=True,
        max_length=32,
        null=False,
        blank=False,
        verbose_name='机房')
    host = models.CharField(
        db_index=True,
        null=True,
        blank=True,
        max_length=32,
        verbose_name='主机UUID')
