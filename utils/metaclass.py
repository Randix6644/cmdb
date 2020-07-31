from typing import Optional


__all__ = [
    'SingletonMeta'
]


class SingletonMeta(type):
    """
    单例元类
    """

    _instance: Optional[type] = None

    def __call__(cls, *args, **kwargs) -> type:
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance
