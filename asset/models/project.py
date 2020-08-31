from django.db import models
from utils import DeleteObjectError
from common.models import ManageModel
from . import Host


__all__ = ['Project']


class Project(ManageModel):
    class Meta:
        db_table = 'project'
        verbose_name = '项目'
        ordering = ('created_at',)

    name = models.CharField(max_length=255, verbose_name='名字')
    enabled = models.BooleanField(default=True, verbose_name='是否启用')
    comment = models.TextField(null=True, verbose_name='备注')

    def pre_delete(self):
        host = Host.dao.get_queryset(project=self.uuid)
        if host:
            raise DeleteObjectError(f'Project: {self.uuid} linked to multiple resources, unbind before deleting')
