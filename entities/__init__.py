"""实体模块初始化"""
from .core import Core
from .ship import Ship
from .projectile import Projectile
from .explosion import Explosion
from .map_object import MapObject

__all__ = ['Core', 'Ship', 'Projectile', 'Explosion', 'MapObject']