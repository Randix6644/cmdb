from configparser import ConfigParser


__all__ = ['cfg']


cfg = ConfigParser()
cfg.read('./config.ini')


