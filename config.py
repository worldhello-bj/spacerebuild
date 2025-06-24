"""游戏配置文件"""
from dataclasses import dataclass
from typing import Tuple
from enum import Enum

# 游戏常量
SCREEN_WIDTH = 1800
SCREEN_HEIGHT = 1000
FPS = 60

class ObjectType(Enum):
    """地图物体类型"""
    OBSTACLE = "obstacle"
    RESOURCE = "resource"
    BUFF = "buff"
    DEBUFF = "debuff"

@dataclass
class GameConfig:
    """游戏配置类"""
    # 基础设置
    num_factions: int = 6
    map_objects_count: int = 50
    
    # 核心设置
    core_radius: float = 30.0
    core_mass: float = 100.0
    core_initial_velocity_range: Tuple[float, float] = (20.0, 50.0)
    core_spawn_ships_interval: int = 120
    core_max_ships: int = 35
    core_health: float = 1500.0
    
    # 舰船设置
    ship_length: float = 24.0
    ship_width: float = 16.0
    ship_speed: float = 95.0
    ship_mass: float = 1.0
    ship_health: float = 120.0
    ship_attack_damage: float = 25.0
    ship_attack_range: float = 280.0
    ship_attack_angle: float = 40.0
    ship_attack_cooldown: int = 50
    ship_turn_rate: float = 3.8
    ship_retreat_heal_rate: float = 12.0
    
    # 物理设置
    gravity_strength: float = 120.0
    friction: float = 0.98
    boundary_bounce: float = 0.85
    
    # 地图对象设置
    obstacle_size_range: Tuple[float, float] = (35.0, 90.0)
    resource_size_range: Tuple[float, float] = (18.0, 35.0)
    buff_size_range: Tuple[float, float] = (12.0, 18.0)
    debuff_size_range: Tuple[float, float] = (12.0, 18.0)