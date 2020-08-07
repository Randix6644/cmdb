from django.db import models
from common.models import DisplayModel


__all__ = ['MonitorData']


class MonitorData(DisplayModel):
    """
    抽象监控模型
    """
    class Meta:
        db_table = 'monitor_data'
        verbose_name = '主机监控信息'
        unique_together = ('host', 'metric', 'time')

    value = models.FloatField(verbose_name='指标值')
    time = models.DateTimeField(verbose_name='监控时间')

    # 逻辑外键
    metric = models.CharField(max_length=32, verbose_name='指标')
    host = models.CharField(max_length=32, verbose_name='主机')


