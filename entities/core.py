"""核心基地类"""
import pygame
import math
import random
from typing import List, TYPE_CHECKING
from utils.vector2 import Vector2
from utils.colors import *
from config import GameConfig, SCREEN_WIDTH, SCREEN_HEIGHT

if TYPE_CHECKING:
    from entities.ship import Ship
    from entities.map_object import MapObject
    from game.simulator import SpaceWarSimulator

class Core:
    """阵营核心基地"""
    
    def __init__(self, pos: Vector2, faction_id: int, config: GameConfig):
        self.pos = pos
        self.velocity = Vector2(
            random.uniform(-config.core_initial_velocity_range[0], config.core_initial_velocity_range[1]),
            random.uniform(-config.core_initial_velocity_range[0], config.core_initial_velocity_range[1])
        )
        self.faction_id = faction_id
        self.radius = config.core_radius
        self.mass = config.core_mass
        self.ships: List['Ship'] = []
        self.spawn_timer = 0
        self.max_ships = config.core_max_ships
        self.spawn_interval = config.core_spawn_ships_interval
        self.health = config.core_health
        self.max_health = config.core_health
        self.resources = 100.0
        self.ship_production_cost = 25.0
        self.damage_flash_timer = 0
        
        # 护盾系统
        self.shield_energy = 100.0
        self.max_shield = 100.0
        self.shield_recharge_rate = 5.0
        
        # 统计数据
        self.total_kills = 0
        self.total_damage_dealt = 0.0
        self.total_damage_taken = 0.0
        
    def update(self, config: GameConfig, map_objects: List['MapObject'], other_cores: List['Core']):
        """更新核心状态"""
        if self.health <= 0:
            return
            
        self._apply_physics(config, map_objects, other_cores)
        self._handle_boundaries(config)
        self._update_systems()
        self._try_spawn_ship(config)
        
    def _apply_physics(self, config: GameConfig, map_objects: List['MapObject'], other_cores: List['Core']):
        """应用物理效果"""
        forces = Vector2(0, 0)
        
        # 核心间的引力
        for other in other_cores:
            if other != self and other.health > 0:
                direction = other.pos - self.pos
                dist = max(direction.magnitude(), 1.0)
                force_magnitude = (config.gravity_strength * self.mass * other.mass) / (dist * dist)
                forces += direction.normalized() * force_magnitude
                
        # 障碍物排斥力
        for obj in map_objects:
            if obj.type.value == "obstacle":
                direction = self.pos - obj.pos
                dist = max(direction.magnitude(), 1.0)
                if dist < self.radius + obj.size + 60:
                    forces += direction.normalized() * (6000.0 / (dist * dist))
                    
        # 更新速度和位置
        self.velocity = (self.velocity + (forces / self.mass) / 60) * config.friction
        
        if self.velocity.magnitude() > 120.0:
            self.velocity = self.velocity.normalized() * 120.0
            
        self.pos += self.velocity / 60
        
    def _handle_boundaries(self, config: GameConfig):
        """处理边界碰撞"""
        if self.pos.x - self.radius < 0: 
            self.pos.x = self.radius
            self.velocity.x *= -config.boundary_bounce
        elif self.pos.x + self.radius > SCREEN_WIDTH: 
            self.pos.x = SCREEN_WIDTH - self.radius
            self.velocity.x *= -config.boundary_bounce
            
        if self.pos.y - self.radius < 0: 
            self.pos.y = self.radius
            self.velocity.y *= -config.boundary_bounce
        elif self.pos.y + self.radius > SCREEN_HEIGHT: 
            self.pos.y = SCREEN_HEIGHT - self.radius
            self.velocity.y *= -config.boundary_bounce
            
    def _update_systems(self):
        """更新系统状态"""
        # 护盾充能
        if self.shield_energy < self.max_shield:
            self.shield_energy = min(self.max_shield, self.shield_energy + self.shield_recharge_rate / 60)
        
        # 资源增长
        self.resources = min(self.resources + 0.15, 250.0)
        
        # 伤害闪烁
        if self.damage_flash_timer > 0:
            self.damage_flash_timer -= 1
            
    def _try_spawn_ship(self, config: GameConfig):
        """尝试生产舰船"""
        if len(self.ships) < self.max_ships and self.resources >= self.ship_production_cost:
            self.spawn_timer += 1
            if self.spawn_timer >= self.spawn_interval:
                self.spawn_ship(config)
                self.spawn_timer = 0
                self.resources -= self.ship_production_cost
                
    def spawn_ship(self, config: GameConfig):
        """生产新舰船"""
        from entities.ship import Ship
        angle = random.uniform(0, 2 * math.pi)
        spawn_pos = self.pos + Vector2(math.cos(angle), math.sin(angle)) * (self.radius + 40)
        self.ships.append(Ship(spawn_pos, self.faction_id, config))
        
    def take_damage(self, damage: float, simulator: 'SpaceWarSimulator'):
        """受到伤害"""
        if self.health <= 0: 
            return
            
        # 护盾吸收部分伤害
        if self.shield_energy > 0:
            shield_absorbed = min(self.shield_energy, damage * 0.6)
            self.shield_energy -= shield_absorbed
            damage -= shield_absorbed
            
        self.health -= damage
        self.total_damage_taken += damage
        self.damage_flash_timer = 8
        
        # 核心被摧毁
        if self.health <= 0:
            self.health = 0
            self.ships.clear()
            self._create_destruction_effect(simulator)
            
    def _create_destruction_effect(self, simulator: 'SpaceWarSimulator'):
        """创建摧毁特效"""
        from entities.explosion import Explosion
        color = FACTION_COLORS[self.faction_id % len(FACTION_COLORS)]
        explosion = Explosion(
            self.pos, 
            color, 
            num_particles=300, 
            particle_size_range=(5, 15), 
            duration_range=(120, 240)
        )
        simulator.effects.append(explosion)
        simulator.screen_shake = 15
        
    def draw(self, screen):
        """绘制核心"""
        if self.health <= 0:
            return
            
        color = FACTION_COLORS[self.faction_id % len(FACTION_COLORS)]
        
        # 绘制护盾
        self._draw_shield(screen)
        
        # 脉冲效果
        self._draw_pulse_effect(screen, color)
        
        # 主体核心
        self._draw_core_body(screen, color)
        
        # 状态条
        self._draw_status_bars(screen)
        
    def _draw_shield(self, screen):
        """绘制护盾效果"""
        if self.shield_energy > 0:
            shield_alpha = int(120 * (self.shield_energy / self.max_shield))
            shield_radius = self.radius + 8
            shield_surface = pygame.Surface((shield_radius * 2, shield_radius * 2), pygame.SRCALPHA)
            shield_color = (100, 200, 255, shield_alpha)
            pygame.draw.circle(shield_surface, shield_color, (shield_radius, shield_radius), shield_radius, 3)
            screen.blit(shield_surface, (self.pos.x - shield_radius, self.pos.y - shield_radius))
    
    def _draw_pulse_effect(self, screen, color):
        """绘制脉冲效果"""
        pulse_alpha = (math.sin(pygame.time.get_ticks() * 0.003) + 1) / 2 * 80 + 40
        pulse_radius = self.radius * 1.4
        pulse_surface = pygame.Surface((pulse_radius * 2, pulse_radius * 2), pygame.SRCALPHA)
        pulse_color = (color[0], color[1], color[2], int(pulse_alpha))
        pygame.draw.circle(pulse_surface, pulse_color, (pulse_radius, pulse_radius), pulse_radius)
        screen.blit(pulse_surface, (self.pos.x - pulse_radius, self.pos.y - pulse_radius))
    
    def _draw_core_body(self, screen, color):
        """绘制核心主体"""
        final_color = WHITE if self.damage_flash_timer > 0 else color
        pygame.draw.circle(screen, final_color, (int(self.pos.x), int(self.pos.y)), int(self.radius))
        pygame.draw.circle(screen, WHITE, (int(self.pos.x), int(self.pos.y)), int(self.radius), 4)
        
        # 内部发光环
        inner_radius = int(self.radius * 0.7)
        inner_surface = pygame.Surface((inner_radius * 2, inner_radius * 2), pygame.SRCALPHA)
        inner_color = (255, 255, 255, 150)
        pygame.draw.circle(inner_surface, inner_color, (inner_radius, inner_radius), inner_radius)
        screen.blit(inner_surface, (int(self.pos.x - inner_radius), int(self.pos.y - inner_radius)))
    
    def _draw_status_bars(self, screen):
        """绘制状态条"""
        bar_width, bar_height = 100, 12
        bar_x, bar_y = self.pos.x - bar_width // 2, self.pos.y - self.radius - 35
        
        # 血量条背景和前景
        pygame.draw.rect(screen, (40, 40, 40), (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4))
        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, bar_width * (self.health / self.max_health), bar_height))
        
        # 护盾条
        shield_y = bar_y - 16
        pygame.draw.rect(screen, (20, 20, 60), (bar_x, shield_y, bar_width, 6))
        pygame.draw.rect(screen, (100, 200, 255), (bar_x, shield_y, bar_width * (self.shield_energy / self.max_shield), 6))