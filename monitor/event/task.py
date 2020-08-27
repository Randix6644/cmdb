from abc import ABC, abstractmethod
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from utils import generate_unique_uuid


class BaseTask(ABC):
    """
    任务抽象类，任务实例化后作为 job 在调度器中执行
    """

    _channel_layer = get_channel_layer()
    _status = (
        '运行中',
        '成功',
        '失败'
    )
    _step = (
        '开始',
        '结束'
    )

    def __init__(self):
        """
        初始化作业 id
        """
        self.id = generate_unique_uuid()
        self.result = None

    @property
    @abstractmethod
    def name(self):
        """
        作业名称
        """
        pass

    @abstractmethod
    def _run(self):
        """
        作业执行具体内容
        """
        pass

    def run(self):
        """
        作业执行入口，开始和结束加入进度通知
        """
        self._notice_progress(0, 0)
        try:
            self.result = self._run()
        except BaseException as e:
            print(f'job error: {e.__repr__()}')
            self.result = e
            self._notice_progress(2, len(self._step) - 1)
        self._notice_progress(1, len(self._step) - 1)

    def _notice_progress(self, status, step):
        """
        通知作业进度
        :param status: 状态号
        :param step: 步骤号
        """
        group_name = f'job_{self.id}'
        async_to_sync(self._channel_layer.group_send)(group_name, {
            'type': 'chat.message',
            'status': self._status[status],
            'step': self._step[step],
            'progress': f'{step * 100 // (len(self._step) - 1)}%'
        })
