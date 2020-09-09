from __future__ import annotations
from typing import List
from concurrent.futures import ProcessPoolExecutor
from abc import ABC, abstractmethod
from cmdb.settings import BASE_DIR
from utils import logger
import os
from .sdk import PBExecutor, ModelResultsCollector, CallbackBase

__all__ = ['CollectorFactory', 'LinuxCollectorFactory', 'linux_collector_factory_run_with_process']


def linux_collector_factory_run_with_process(addr: List, pb: List, log_str, extra_args=None, **kwargs):
    try:
        with ProcessPoolExecutor(max_workers=1) as executor:
            future = executor.submit(LinuxCollectorFactory().exec, addr, pb, extra_args, **kwargs)
            rst = future.result()
            return rst
    except Exception as e:
        logger.error(f"unable to execute {log_str}, err: {e}")
        raise Exception(f"unable to execute {log_str}, err: {e}")


class CollectorFactory:
    def create_collector(self) -> Collector:
        pass

    def exec(self, hosts, playbooks, extra_args=None, **kwargs) -> dict:
        creator = self.create_collector()
        creator.callback = ModelResultsCollector()
        creator.hosts = hosts
        creator.playbooks = playbooks
        creator.execute(extra_args, **kwargs)
        creator.set_ok()
        creator.set_failed()
        creator.set_unreachable()
        return creator.result


class LinuxCollectorFactory(CollectorFactory):
    def create_collector(self) -> Collector:
        creator = LinuxCollector()
        return creator


class Collector(ABC):
    _result_raw = {'success': {}, 'failed': {}, 'unreachable': {}}
    _res = {}
    _callback = None
    hosts = []
    _pbs = None

    @property
    def result(self):
        return self._result_raw

    @property
    def playbooks(self):
        return self._pbs

    @playbooks.setter
    def playbooks(self, pbs):
        os.chdir(BASE_DIR)
        for pb in pbs:
            if not os.path.isfile(pb):
                raise FileNotFoundError()
        self._pbs = pbs

    @property
    def callback(self):
        return self._callback

    @callback.setter
    def callback(self, callback):
        if not isinstance(callback, CallbackBase):
            raise Exception('not valid callback')
        self._callback = callback

    @abstractmethod
    def execute(self, extra_args: dict = None, **kwargs):
        pass

    @abstractmethod
    def set_ok(self):
        pass

    @abstractmethod
    def set_failed(self):
        pass

    @abstractmethod
    def set_unreachable(self):
        pass


class LinuxCollector(Collector):
    def execute(self, extra_args: dict = None, **kwargs):
        self._res = PBExecutor(
            self.playbooks,
            self.hosts,
            self.callback,
            extra_args
        )(**kwargs)

    def set_ok(self):
        for host, result in self._res.host_ok.items():
            self._result_raw['success'][host] = {}
            for task_name, fact in result.items():
                if task_name == 'Gathering Facts':
                    continue
                af = fact._result.get('ansible_facts')
                if not af:
                    continue
                for k, v in af.items():
                    self._result_raw['success'][host][k] = v

    def set_failed(self):
        for host, result in self._res.host_failed.items():
            self._result_raw['failed'][host] = {}
            for task_name, fact in result.items():
                if fact._result.get('stderr'):
                    raise Exception(f'failed to execute task{task_name} on {host}, err:{fact._result.get("stderr")}')

    def set_unreachable(self):
        for host, result in self._res.host_unreachable.items():
            self._result_raw['unreachable'][host] = {}
            for task_name, fact in result.items():
                raise Exception(f'failed to execute task: {task_name}, err: host:{host} unreachable')
                # if not fact._result:
                #     break
