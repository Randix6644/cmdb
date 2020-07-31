from django.db import models
from common.models import ManageModel


class IDC(ManageModel):
    class Meta:
        db_table = 'idc'
    name = models.CharField(index=True, max_length=64, verbose_name='idc名称')
    region = models.CharField(index=True, max_length=64, verbose_name='地区')
    is_enabled = models.BooleanField(default=True, verbose_name="是否激活")

