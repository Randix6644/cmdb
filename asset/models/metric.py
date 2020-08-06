from django.db import models
from common.models import ManageModel

__all__ = ['Metric']


class Metric(ManageModel):
    class Meta:
        db_table = 'metric'
    name = models.CharField(db_index=True, max_length=64, verbose_name='指标名称')
    comment = models.CharField(max_length=64, verbose_name='指标描述', null=True, blank=True)

