from utils import CreateObjectError, logger
from cmdb.configs import CFG
from asset.models import *
from monitor.event import BaseTask
from monitor.factory import linux_collector_factory_run_with_process

__all__ = ['HardwareSync']


class HardwareSync(BaseTask):
    @property
    def name(self):
        return '[同步监控数据]'

    def _run(self):
        pb = CFG.get('ansible', 'monitor_pb')
        ips = IP.dao.get_queryset(used_to_sync=True)
        for ip in ips:
            host_obj: Host = Host.dao.get_obj(uuid=ip.host)
            user = host_obj.username
            addr = f'{ip.address}:{host_obj.ssh_port}'
            host_info = linux_collector_factory_run_with_process(
                [addr], [pb], 'host data sync', user=user)
            cpu = host_info['success'][ip.address]
            model = str(host_info['success'][ip]['cpu'][2])
            mem = host_info['success'][ip]['ram']
            hard_disk_set = host_info['success'][ip]['disk']
            os = host_info['success'][ip]['release']
            pass
