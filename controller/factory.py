from __future__ import annotations
from abc import ABC, abstractmethod
from cmdb.settings import BASE_DIR
import os
from .sdk import PBExecutor, ModelResultsCollector, CallbackBase


class CollectorFactory:
    def create_collector(self) -> Collector:
        pass

    def exec(self, hosts, playbooks, extra_args=None) -> dict:
        creator = self.create_collector()
        creator.callback = ModelResultsCollector()
        creator.hosts = hosts
        creator.playbooks = playbooks
        creator.execute(extra_args)
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

    def __init__(self, *args, **kwargs):
        pass

    @property
    def result(self):
        return self._res

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
    def execute(self, extra_args: dict = None):
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
    def execute(self, extra_args: dict = None):
        self._res = PBExecutor(
            self.playbooks,
            self.hosts,
            self.callback,
            extra_args
        )()

    def set_ok(self):
        for host, result in self._res.host_ok.items():
            self._result_raw['success'][host] = {}
            for i in range(0, len(result)):
                if i == 0:
                    continue
                if not result[i]._result.get('ansible_facts'):
                    continue
                for k, v in result[i]._result.get('ansible_facts').items():
                    self._result_raw['success'][host][k] = v

    def set_failed(self):
        pass

    def set_unreachable(self):
        pass
