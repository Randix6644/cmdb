from django.db import models
from common.models import DisplayModel


__all__ = ['Project']


class Project(DisplayModel):
    class Meta:
        db_table = 'project'
        verbose_name = '项目'
        ordering = ('idc', 'name', 'enable')

    name = models.CharField(max_length=255, verbose_name='名字')
    enabled = models.BooleanField(default=True, verbose_name='是否启用')
    comment = models.TextField(null=True, verbose_name='备注')

