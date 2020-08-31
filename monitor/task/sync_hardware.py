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
        pass