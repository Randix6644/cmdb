from controller.configs import *
from asset.models import *


playbooks = cfg.get(
    'ansible',
    'pb_path'
)
inventory = cfg.get(
    'ansible',
    'pb_path'
)

def initialize():
    pass