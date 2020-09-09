from django.db import models
from common.models import DisplayModel


class DiskHost(DisplayModel):
    class Meta:
        db_table = 'disk_host'
        ordering = ('-created_at',)
        unique_together = ('disk_id', 'host_id',)

    disk_id = models.CharField(max_length=32)
    host_id = models.CharField(max_length=32)
