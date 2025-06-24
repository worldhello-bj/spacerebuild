"""地图物体类"""
import pygame
import random
import math
from typing import List, Tuple
from utils.vector2 import Vector2
from utils.colors import *
from config import ObjectType

class MapObject:
    """地图上的物体（障碍物、资源、增益/减益道具）"""
    
    def __init__(self, pos: Vector2, size: float, obj_type: ObjectType):
        self.pos = pos
        self.size = size
        self.type = obj_type
        self.active = True
        self.animation_timer = random.uniform(0, 2 * math.pi)
        
        # 根据类型设置属性
        self._setup_type_attributes()
        
        # 为障碍物创建形状
        if obj_type == ObjectType.OBSTACLE: 
            self.shape_points = self._create_asteroid_shape()
            
    def _setup_type_attributes(self):
        """根据类型设置属性"""
        if self.type == ObjectType.RESOURCE: 
            self.effect_value = 60.0
        elif self.type == ObjectType.BUFF: 
            self.effect_value = 1.6
            self.effect_duration = 360
        elif self.type == ObjectType.DEBUFF: 
            self.effect_value = 0.4
            self.effect_duration = 240
            
    def _create_asteroid_shape(self) -> List[Tuple[float, float]]:
        """创建小行星形状"""
        points = []
        num_vertices = random.randint(8, 14)
        for i in range(num_vertices):
            angle = (i / num_vertices) * 2 * math.pi
            dist = self.size * random.uniform(0.7, 1.3)
            points.append((
                self.pos.x + math.cos(angle) * dist, 
                self.pos.y + math.sin(angle) * dist
            ))
        return points
        
    def update(self):
        """更新动画"""
        self.animation_timer += 0.02
        
    def draw(self, screen):
        """绘制地图物体"""
        if self.type == ObjectType.OBSTACLE:
            self._draw_asteroid(screen)
        else:
            self._draw_interactive_object(screen)
            
    def _draw_asteroid(self, screen):
        """绘制小行星"""
        # 阴影
        shadow_points = [(p[0] + 2, p[1] + 2) for p in self.shape_points]
        pygame.draw.polygon(screen, (30, 30, 30), shadow_points)
        
        # 主体
        pygame.draw.polygon(screen, GRAY, self.shape_points)
        pygame.draw.polygon(screen, LIGHT_GRAY, self.shape_points, 3)
        
    def _draw_interactive_object(self, screen):
        """绘制可交互物体"""
        color_map = {
            ObjectType.RESOURCE: (GREEN, (0, 255, 100)),
            ObjectType.BUFF: (YELLOW, (255, 255, 100)),
            ObjectType.DEBUFF: (PURPLE, (200, 100, 255))
        }
        color, glow_color = color_map.get(self.type, (WHITE, WHITE))
        
        # 动态发光效果
        pulse = math.sin(self.animation_timer) * 0.3 + 0.7
        self._draw_glow_effect(screen, glow_color, pulse)
        self._draw_main_body(screen, color, pulse)
        self._draw_inner_glow(screen, pulse)
        
    def _draw_glow_effect(self, screen, glow_color, pulse):
        """绘制发光效果"""
        glow_radius = int(self.size * 1.8 * pulse)
        glow_alpha = int(80 * pulse)
        
        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        glow_color_with_alpha = (glow_color[0], glow_color[1], glow_color[2], glow_alpha)
        pygame.draw.circle(glow_surface, glow_color_with_alpha, (glow_radius, glow_radius), glow_radius)
        screen.blit(glow_surface, (int(self.pos.x - glow_radius), int(self.pos.y - glow_radius)))
        
    def _draw_main_body(self, screen, color, pulse):
        """绘制主体"""
        pygame.draw.circle(screen, color, (int(self.pos.x), int(self.pos.y)), int(self.size))
        pygame.draw.circle(screen, WHITE, (int(self.pos.x), int(self.pos.y)), int(self.size), 2)
        
    def _draw_inner_glow(self, screen, pulse):
        """绘制内部发光"""
        inner_size = int(self.size * 0.6)
        inner_alpha = int(150 * pulse)
        inner_surface = pygame.Surface((inner_size * 2, inner_size * 2), pygame.SRCALPHA)
        inner_color = (255, 255, 255, inner_alpha)
        pygame.draw.circle(inner_surface, inner_color, (inner_size, inner_size), inner_size)
        screen.blit(inner_surface, (int(self.pos.x - inner_size), int(self.pos.y - inner_size)))