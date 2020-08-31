from ansible import context
from ansible.cli import CLI
from ansible.plugins.callback import CallbackBase
from ansible.module_utils.common.collections import ImmutableDict
# from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from typing import List, Type
from monitor.modified_ansible.custom_pb_executor import PlaybookExecutor
from ansible.executor.task_result import TaskResult

__all__ = ['ModelResultsCollector', 'PBExecutor']


class ModelResultsCollector(CallbackBase):
    def __init__(self, *args, **kwargs):
        super(ModelResultsCollector, self).__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}

    def gather_result(self, status, rst):
        try:
            d = getattr(self, f'host_{status}')
        except AttributeError as e:
            raise Exception('invalid status')
        if not d.get(rst._host.get_name()):
            d[rst._host.get_name()] = {}
        d[rst._host.get_name()][rst.task_name] = rst

    def v2_runner_on_unreachable(self, rst):
        self.gather_result('unreachable', rst)

    def v2_runner_on_ok(self, rst):
        self.gather_result('ok', rst)

    def v2_runner_on_failed(self, rst, ignore_errors=False):
        self.gather_result('failed', rst)


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
            connection='smart',
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
            inventory.add_host(
                host=host.split(':')[0],
                port=host.split(':')[1],
                group='once')
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
