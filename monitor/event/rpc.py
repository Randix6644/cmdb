from zerorpc import Server, Client
from monitor.event.scheduler import SchedulerServer
from utils import SingletonMeta
from threading import Lock
from django.conf import settings


class RPCServer:
    """
    事件 rpc 服务端
    """

    endpoint = f'tcp://{settings.CFG.get("rpc","RPC_BIND")}:{settings.CFG.get("rpc", "RPC_PORT")}'
    print(endpoint)

    def __init__(self):
        """
        初始化，启动调度系统和 rpc 服务
        """
        self._scheduler_srv = SchedulerServer()
        self._server = Server(self._scheduler_srv)
        self._server.bind(self.endpoint)

    def run(self):
        """
        启动 rpc 服务
        """
        self._server.run()


class RPCClient:
    """
    事件 rpc 客户端
    """

    endpoint = f'tcp://{settings.CFG.get("rpc", "RPC_HOST")}:{settings.CFG.get("rpc", "RPC_PORT")}'
    print(endpoint)

    def __init__(self):
        """
        初始化
        """
        self._client = Client()

    def __getattr__(self, item):
        """
        设置调用传递到客户端
        """
        return getattr(self._client, item)

    def __enter__(self):
        """
        进入自动连接
        """
        self._client.connect(self.endpoint)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        退出时自动断开，并重置客户端
        """
        self._client.close()


class ThreadingRPCClient(metaclass=SingletonMeta):
    """
    多线程安全的事件 rpc 客户端
    """

    endpoint = f'tcp://{settings.CFG.get("rpc", "RPC_HOST")}:{settings.CFG.get("rpc", "RPC_PORT")}'

    def __init__(self):
        """
        初始化
        """
        self._client = Client()
        self._lock = Lock()
        self._enter_num = 0

    def __getattr__(self, item):
        """
        设置调用传递到客户端
        """
        return getattr(self._client, item)

    def __enter__(self):
        """
        当进入的线程为 0 时，重置客户端并自动连接
        """
        with self._lock:
            if self._enter_num == 0:
                self._client = Client()
                self._client.connect(self.endpoint)
            self._enter_num += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        退出时自动断开，并重置客户端
        """
        with self._lock:
            self._enter_num -= 1
            if self._enter_num == 0:
                self._client.close()
        self._client = Client()

