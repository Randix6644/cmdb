from configparser import ConfigParser


__all__ = ['CFG']


CFG = ConfigParser()
CFG.read('cmdb/configs/config.ini')


