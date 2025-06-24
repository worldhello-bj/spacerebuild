"""爆炸效果类"""
import pygame
import random
import math
from utils.vector2 import Vector2
from typing import Tuple
from config import FPS

class Explosion:
    """爆炸特效类"""
    
    def __init__(self, pos: Vector2, color: Tuple[int, int, int], 
                 num_particles: int = 150, 
                 particle_size_range: Tuple[int, int] = (3, 8), 
                 duration_range: Tuple[int, int] = (60, 120)):
        
        self.particles = []
        for _ in range(num_particles):
            p_pos = Vector2(pos.x, pos.y)
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(20, 150)
            p_vel = Vector2(math.cos(angle), math.sin(angle)) * speed
            p_size = random.uniform(*particle_size_range)
            p_lifetime = random.randint(*duration_range)
            
            # 颜色变化
            particle_color = (
                min(255, max(0, color[0] + random.randint(-30, 30))),
                min(255, max(0, color[1] + random.randint(-30, 30))),
                min(255, max(0, color[2] + random.randint(-30, 30)))
            )
            self.particles.append([p_pos, p_vel, p_size, p_lifetime, particle_color])
            
    def update(self):
        """更新粒子状态"""
        for p in self.particles:
            p[0] += p[1] / FPS
            p[1] *= 0.96  # 阻力
            p[3] -= 1
        self.particles = [p for p in self.particles if p[3] > 0]
        
    def draw(self, screen):
        """绘制爆炸效果"""
        for pos, vel, size, lifetime, color in self.particles:
            alpha = max(0, min(255, int(255 * (lifetime / 120))))
            size_int = max(1, int(size))
            
            temp_surface = pygame.Surface((size_int*2, size_int*2), pygame.SRCALPHA)
            rgba_color = (color[0], color[1], color[2], alpha)
            pygame.draw.circle(temp_surface, rgba_color, (size_int, size_int), size_int)
            screen.blit(temp_surface, (int(pos.x - size), int(pos.y - size)))