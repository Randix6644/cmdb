from ansible import context
from ansible.cli import CLI
from ansible.plugins.callback import CallbackBase
from ansible.module_utils.common.collections import ImmutableDict
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from typing import List, Type

__all__ = ['ModelResultsCollector', 'PBExecutor']


class ModelResultsCollector(CallbackBase):
    def __init__(self, *args, **kwargs):
        super(ModelResultsCollector, self).__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}

    def v2_runner_on_unreachable(self, rst):
        self.host_unreachable[rst._host.get_name()] = rst

    def v2_runner_on_ok(self, rst):
        if not self.host_ok.get(rst._host.get_name()):
            self.host_ok[rst._host.get_name()] = []
        self.host_ok[rst._host.get_name()].append(rst)

    def v2_runner_on_failed(self, rst, ignore_errors=False):
        self.host_failed[rst._host.get_name()] = rst


class PBExecutor:
    def __init__(
            self,
            playbooks: List,
            hosts: List,
            cb: CallbackBase,
            extra_vars: dict = None,
            inventory_path: str = None):
        self.pb = playbooks
        self.inventory = inventory_path if inventory_path else 'localhost'
        self.extra_vars = extra_vars if extra_vars else {}
        self.hosts = hosts
        self.cb = cb

    def __call__(self, *args, **kwargs):
        loader = DataLoader()
        user = kwargs.get('user', 'root')
        become = kwargs.get('become', False)
        become_method = kwargs.get('become_method', None)
        become_user = kwargs.get('become_user', None)
        context.CLIARGS = ImmutableDict(
            tags={},
            listtags=False,
            listtasks=False,
            listhosts=False,
            syntax=False,
            connection='ssh',
            module_path=None,
            forks=100,
            remote_user=user,
            private_key_file=None,
            ssh_common_args=None,
            ssh_extra_args=None,
            sftp_extra_args=None,
            scp_extra_args=None,
            become=become,
            become_method=become_method,
            become_user=become_user,
            verbosity=True,
            check=False,
            start_at_task=None)

        inventory = InventoryManager(
            loader=loader, sources=(
                self.inventory,))
        inventory.add_group('once')
        for host in self.hosts:
            inventory.add_host(host=host, group='once')
        variable_manager = VariableManager(
            loader=loader,
            inventory=inventory,
            version_info=CLI.version_info(
                gitinfo=False))
        self.extra_vars['once'] = 'once'
        variable_manager._extra_vars = self.extra_vars
        pb_ex = PlaybookExecutor(
            playbooks=self.pb,
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            passwords={})
        pb_ex._tqm._stdout_callback = self.cb
        pb_ex.run()
        return self.cb

#
# callback = ModelResultsCollector()
# res = PBExecutor(
#     ['/Users/randix/work/python_projects/cmdb/asset/task/facts.yml'],
#     ['124.71.104.101', '47.106.12.55'], callback)()
#


# class Processor:
#     def __init__(self, res):
#         self._result_raw = {'success': {}, 'failed': {}, 'unreachable': {}}
#         self.res = res
#
#     @property
#     def result(self):
#         return self._result_raw
#
#     def get_ok(self):
#         for host, result in self.res.host_ok.items():
#             self._result_raw['success'][host] = {}
#             for i in range(0, len(result)):
#                 if i == 0:
#                     continue
#                 if not result[i]._result.get('ansible_facts'):
#                     continue
#                 for k, v in result[i]._result.get('ansible_facts').items():
#                     self._result_raw['success'][host][k] = v
#
#     def get_failed(self):
#         pass
#
#     def get_unreachable(self):
#         pass
#
#
# for host, result in res.host_failed.items():
#     result_raw['failed'][host] = result._result
# for host, result in res.host_unreachable.items():
#     result_raw['unreachable'][host] = result._result
#
