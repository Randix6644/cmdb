from django.db import models
from common.models import DisplayModel
# from django_apscheduler


__all__ = ['JobHistory']


class JobHistory(DisplayModel):
    """
    任务历史记录
    """
    class Meta:
        db_table = 'job_history'
        verbose_name = '任务历史信息'
        unique_together = ('host', 'metric', 'time')

    type = models.SmallIntegerField(verbose_name='记录类型')
    msg = models.CharField(verbose_name='额外消息', blank=True)

    # 逻辑外键
    id = models.IntegerField(verbose_name='作业id')


