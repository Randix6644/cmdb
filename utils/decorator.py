from typing import Optional, Callable
from threading import Thread
from functools import update_wrapper
from django.db import transaction
import ctypes


__all__ = [
    'ThreadBasedTimeoutControl'
]


class ThreadBasedTimeoutControl:
    """
    基于线程的超时控制装饰器
    """

    def __init__(self, timeout: Optional[int] = 3600):
        """
        初始化
        :param timeout: 超时时间，单位秒
        """
        self._timeout = timeout

    @staticmethod
    def _async_raise(tid: int, exc_class: type):
        """
        触发指定线程中触发异常
        :param tid: 线程 id
        :param exc_class: 异常类
        """
        if not isinstance(exc_class, type):
            raise TypeError("Only class can be raised (not instances)")

        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(exc_class))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            # 结果非 0 则表示发送错误，重新调用并使异常为空来恢复效果
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)
            raise SystemError("PyThreadState_SetAsyncExc failed")

    def __call__(self, func: Callable) -> Callable:
        """
        装饰器入口，函数被包装在子线程中运行
        :param func: 被装饰函数
        """
        def _wrapper(*args, **kwargs):

            class ThreadWithReturn(Thread):
                """
                带返回的线程
                """

                def __init__(self, *init_args, **init_kwargs):
                    """
                    初始化错误和返回
                    """
                    super().__init__(*init_args, **init_kwargs)
                    self._exc = None
                    self._result = None

                def run(self):
                    try:
                        if self._target:
                            # 加入 model 自动回滚
                            with transaction.atomic():
                                self._result = self._target(*self._args, **self._kwargs)
                    except BaseException as e:
                        self._exc = e
                    finally:
                        del self._target, self._args, self._kwargs

                @property
                def result(self):
                    """
                    触发异常或获取结果
                    """
                    if self._exc:
                        raise self._exc
                    else:
                        return self._result

            # 执行并阻塞
            t = ThreadWithReturn(target=func, args=args, kwargs=kwargs)
            t.setDaemon(True)
            t.start()
            t.join(self._timeout)

            # 强制结束或返回结果
            if t.is_alive():
                self._async_raise(t.ident, SystemExit)
                raise Exception(f'Job run timeout, more than {self._timeout} s')
            else:
                return t.result

        update_wrapper(_wrapper, func)
        return _wrapper
