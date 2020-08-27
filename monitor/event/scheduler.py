from utils import SingletonMeta, dynamic_import_class
from django.conf import settings
from django_apscheduler.jobstores import DjangoJobStore, register_events
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
from utils import logger


class SchedulerServer(metaclass=SingletonMeta):
    """
    事件调度器
    """

    def __init__(self) -> None:
        """
        初始化，配置并启动调度器
        """
        self._scheduler = BackgroundScheduler(**{
            # 存储器配置
            'jobstores': {
                'default': DjangoJobStore()
            },
            # 运行器配置
            'executors': {
                'default': ThreadPoolExecutor(max_workers=20),
                'process': ProcessPoolExecutor(max_workers=20)
            },
            # 任务默认配置
            'job_defaults': {
                # 一分钟的任务超时冗余
                'misfire_grace_time': 60,
                # 合并积攒的任务
                'coalesce': True,
                # 同一任务的最大并发
                'max_instances': 1
            },
            # 使用 aps 的默认日志器
            'logger': None,
            # 使用 django 的时区
            'time_zone': settings.TIME_ZONE,
            # 存储器访问失败时的尝试间隔
            'jobstore_retry_interval': 10,
        })

        # # 为调度器添加监听器，用于记录任务执行情况
        # register_events(self._scheduler)
        self.add_listener()

        # 启动调度器
        self._scheduler.start()

    def add_immediate_job(self, job_cls: str, *args, **kwargs) -> dict:
        """
        添加一次性任务
        :param job_cls: 作业类
        :param args: 作业初始化位置参数
        :param kwargs: 作业初始化关键字参数
        :return: 任务名字对应 id 的字段
        """
        # 获取作业类
        job_cls = dynamic_import_class(job_cls)
        job_ins = job_cls(*args, **kwargs)

        # 构造调度器的作业添加参数
        func_kwargs = {
            'func': job_ins.run,
            'args': None,
            'kwargs': None
        }
        job_kwargs = {
            'id': job_ins.id,
            'name': job_ins.name
        }
        trigger_kwargs = {
            'trigger': 'date',
            "run_date": None,
            "timezone": settings.TIME_ZONE
        }

        # 添加作业
        job = self._scheduler.add_job(**{
            **func_kwargs,
            **trigger_kwargs,
            **job_kwargs
        })

        return {
            job.name: job.id
        }

    def add_interval_job(self, job_cls: str, interval_kwargs: dict, *args, **kwargs) -> dict:
        """
        添加间隔性任务
        :param job_cls: 作业类
        :param interval_kwargs: 间隔参数
        :param args: 作业初始化位置参数
        :param kwargs: 作业初始化关键字参数
        :return: 任务名字对应 id 的字段
        """

        # 获取作业类
        print(job_cls)
        job_cls = dynamic_import_class(job_cls)
        print(job_cls)
        job_ins = job_cls(*args, **kwargs)

        # 构造调度器的作业添加参数
        func_kwargs = {
            'func': job_ins.run,
            'args': None,
            'kwargs': None
        }
        job_kwargs = {
            'id': job_ins.id,
            'name': job_ins.name,
            'replace_existing': True
        }
        trigger_kwargs = {
            'trigger': 'interval',
            "start_date": None,
            "timezone": settings.TIME_ZONE,
            **interval_kwargs
        }

        # 添加作业
        job = self._scheduler.add_job(**{
            **func_kwargs,
            **trigger_kwargs,
            **job_kwargs
        })

        return {
            job.name: job.id
        }

    def add_listener(self):
        self._scheduler.add_listener(self.listener, EVENT_JOB_MISSED | EVENT_JOB_ERROR | EVENT_JOB_EXECUTED)

    @staticmethod
    def listener(event):
        if event.code == EVENT_JOB_EXECUTED:
            logger.info(f'{event.job_id} executed successfully')
        elif event.code == EVENT_JOB_ERROR:
            logger.error(f'Failed to execute job: {event.job_id} due to {event.exception}')
        elif event.code == EVENT_JOB_MISSED:
            logger.error(f'Job: {event.job_id} missed to execute due to {event.exception}')

