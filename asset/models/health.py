from django.db import models
from common.models import DisplayModel


__all__ = ['HostMonitorData']


class HostMonitorData:
    """
    抽象监控模型
    """
    class Meta:
        db_table = 'monitor_data'
        verbose_name = '主机监控信息'

    cpu_usage = models.FloatField(verbose_name='主机名称')
    cpu_load = models.FloatField(verbose_name='负载')
    memory_usage = models.FloatField(verbose_name='内存使用量')
    memory_usage_percent = models.FloatField(verbose_name='内存使用率')
    time = models.DateTimeField(verbose_name='监控时间')

    # 逻辑外键
    host = models.CharField(max_length=32, index=True, verbose_name='主机')


class DiskMonitorData:
    """
    抽象监控模型
    """
    class Meta:
        db_table = 'monitor_data'
        verbose_name = '主机监控信息'

    usage = models.FloatField(verbose_name='磁盘使用量')
    usage_percent = models.FloatField(verbose_name='磁盘使用率')
    read = models.IntegerField(verbose_name='读字节数数')
    write = models.IntegerField(verbose_name='写字节数数')
    read_iops = models.IntegerField(verbose_name='读请求数')
    write_iops = models.IntegerField(verbose_name='写请求数')

    time = models.DateTimeField(verbose_name='监控时间')

    # 逻辑外键
    host = models.CharField(max_length=32, index=True, verbose_name='主机')

