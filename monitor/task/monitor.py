from datetime import datetime
from django.utils import timezone
from utils import CreateObjectError, logger
from cmdb.configs import CFG
from asset.models import *
from monitor.event import BaseTask
from monitor.factory import LinuxCollectorFactory

__all__ = ['MonitorSync']


class MonitorSync(BaseTask):
    @property
    def name(self):
        return '[同步监控数据]'

    def _run(self):
        pb = CFG.get('ansible', 'monitor_pb')
        ips = IP.dao.get_queryset(used_to_sync=True)
        metrics = Metric.dao.get_queryset()
        for ip in ips:
            host_obj: Host = Host.dao.get_obj(uuid=ip.host)
            user = host_obj.username
            addr = f'{ip.address}:{host_obj.ssh_port}'
            try:
                host_info = LinuxCollectorFactory().exec(
                    [addr], [pb], user=user)
            except Exception as e:
                logger.error(f"unable to collect host data, err{e}")
                raise Exception(f"unable to collect host data, err{e}")
            for m in metrics:
                try:
                    value = host_info['success'][ip.address][m.name]
                    kwargs = {
                                'value': value,
                                'metric': m.uuid,
                                'host': host_obj.uuid,
                                'time': timezone.now()
                    }
                except KeyError as e:
                    logger.error(f'unable to create monitor_data with {host_info} due to err {e}')
                    continue
                try:
                    MonitorData.dao.create_obj(**kwargs)
                except CreateObjectError as e:
                    logger.error(f'unable to sync metric data for host:{host_obj.uuid}, ip:{ip.address} due to err: {e}')
