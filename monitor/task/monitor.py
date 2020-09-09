from django.utils import timezone
from asset.models.mapping import *
from utils import CreateObjectError, logger
from cmdb.configs import CFG
from asset.models import *
from monitor.event import BaseTask
from monitor.factory import linux_collector_factory_run_with_process

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
            host_info = linux_collector_factory_run_with_process(
                [addr], [pb], 'host', user=user)
            for m in metrics:
                parser = self.parser_factory(m.name)
                try:
                    value = host_info['success'][ip.address][self.get_metric_name(m)]
                except KeyError as e:
                    print(f'holly fuck {host_info}')
                    logger.warning(
                        f'unable to create monitor_data with {host_info} due to err {e}')
                    continue
                rst = parser(value)
                if m.type == MetricTypeMapping.index('disk'):
                    kwargs = []
                    for k, v in rst.items():
                        value = v.get(m.name)
                        one_kwargs = self.new_kwargs(
                            value, m.uuid, host_obj.uuid, k)
                        kwargs.append(one_kwargs)
                else:
                    kwargs = [
                        self.new_kwargs(
                            value, m.uuid, host_obj.uuid)]
                try:
                    MonitorData.dao.bulk_create_obj(kwargs)
                except CreateObjectError as e:
                    logger.error(
                        f'unable to sync metric data for host:{host_obj.uuid}, ip:{ip.address} due to err: {e}')

    @staticmethod
    def get_metric_name(m):
        if m.type == MetricTypeMapping.index('disk'):
            return 'disk_info'
        return m.name

    @staticmethod
    def new_kwargs(value, metric_id, instance, extra_flag=None):
        kwargs = {
            'value': value,
            'metric': metric_id,
            'instance': instance,
            'extra_flag': extra_flag,
            'time': timezone.now()
        }
        return kwargs

    @staticmethod
    def disk_monitor_data_parser(s):
        s = s.replace('\n', ' ')
        data_list = s.split(' ')
        data_list = [i for i in data_list if i and i != ',']
        length = len(data_list)
        d = {}
        for i in range(0, length):
            if i % 6 == 0:
                d[data_list[i]] = {}
                d[data_list[i]]['disk_usage'] = int(data_list[i + 2])/1024/1024
                d[data_list[i]]['disk_avail'] = int(data_list[i + 3])/1024/1024
                d[data_list[i]]['disk_used_percent'] = float(data_list[i + 4].replace('%', '')) / 100
        return d

    @staticmethod
    def host_monitor_data_parser(s):
        return s

    def parser_factory(self, m: str):
        if 'disk' in m:
            return self.disk_monitor_data_parser
        else:
            return self.host_monitor_data_parser
