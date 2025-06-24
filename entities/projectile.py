"""子弹类"""
import pygame
import math
from typing import Union, Tuple, List, TYPE_CHECKING
from utils.vector2 import Vector2
from utils.colors import *
from config import FPS

if TYPE_CHECKING:
    from entities.ship import Ship
    from entities.core import Core
    from game.simulator import SpaceWarSimulator

class Projectile:
    """子弹类"""
    
    def __init__(self, pos: Vector2, target: Union['Ship', 'Core'], 
                 damage: float, color: Tuple[int, int, int]):
        self.pos = pos
        self.target = target
        self.damage = damage
        self.color = color
        self.speed = 600.0
        direction = (target.pos - pos).normalized()
        self.velocity = direction * self.speed
        self.lifetime = 2.8 * FPS
        self.trail_positions = [Vector2(pos.x, pos.y) for _ in range(5)]
        
    def update(self, simulator: 'SpaceWarSimulator'):
        """更新子弹状态"""
        self.pos += self.velocity / FPS
        self.lifetime -= 1
        
        # 更新尾迹
        self.trail_positions.append(Vector2(self.pos.x, self.pos.y))
        if len(self.trail_positions) > 8:
            self.trail_positions.pop(0)
        
        # 屏幕震动
        if self.lifetime < 5 and self.lifetime > 0:
            simulator.screen_shake = 3
            
        if not self.target or self.target.health <= 0:
            self.lifetime = 0
            return
            
        # 碰撞检测
        if self.pos.distance_to(self.target.pos) < 22:
            self.target.take_damage(self.damage, simulator)
            # 命中特效
            from entities.explosion import Explosion
            hit_effect = Explosion(self.pos, self.color, 25, (2, 5), (20, 40))
            simulator.effects.append(hit_effect)
            self.lifetime = 0
            
    def draw(self, screen):
        """绘制子弹和尾迹"""
        # 绘制能量尾迹
        for i, trail_pos in enumerate(self.trail_positions):
            if i > 0:
                alpha = int(255 * (i / len(self.trail_positions)) * 0.8)
                width = max(1, int(4 * (i / len(self.trail_positions))))
                trail_color = (*self.color, alpha)
                
                trail_surface = pygame.Surface((width*2, width*2), pygame.SRCALPHA)
                pygame.draw.circle(trail_surface, trail_color, (width, width), width)
                screen.blit(trail_surface, (trail_pos.x - width, trail_pos.y - width))
        
        # 绘制主弹丸
        glow_surface = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (*self.color, 120), (8, 8), 8)
        screen.blit(glow_surface, (self.pos.x - 8, self.pos.y - 8))
        pygame.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), 3)