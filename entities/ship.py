"""舰船类"""
import pygame
import math
import random
from typing import List, Optional, Union, Tuple, TYPE_CHECKING
from utils.vector2 import Vector2
from utils.colors import *
from config import GameConfig, SCREEN_WIDTH, SCREEN_HEIGHT

if TYPE_CHECKING:
    from entities.core import Core
    from entities.map_object import MapObject
    from game.simulator import SpaceWarSimulator

class Ship:
    """战斗舰船"""
    
    def __init__(self, pos: Vector2, faction_id: int, config: GameConfig):
        # 基础属性
        self.pos = pos
        self.faction_id = faction_id
        self.velocity = Vector2(0, 0)
        self.angle = random.uniform(0, 2 * math.pi)
        
        # 物理属性
        self.length = config.ship_length
        self.width = config.ship_width
        self.speed = config.ship_speed
        self.health = config.ship_health
        self.max_health = config.ship_health
        
        # 战斗属性
        self.attack_damage = config.ship_attack_damage
        self.attack_range = config.ship_attack_range
        self.attack_angle = math.radians(config.ship_attack_angle)
        self.attack_cooldown_max = config.ship_attack_cooldown
        self.attack_cooldown = 0
        
        # AI状态
        self.target: Optional[Union['Ship', 'Core']] = None
        self.state = "patrol"  # patrol, attack_ship, assault_core, retreat
        self.patrol_center = pos
        self.patrol_radius = 180.0
        self.patrol_target = pos
        
        # 效果和状态
        self.buffs: List[Tuple[float, int]] = []
        self.debuffs: List[Tuple[float, int]] = []
        self.damage_flash_timer = 0
        self.is_moving = False
        self.heal_particle_timer = 0
        
        # 统计数据
        self.kills = 0
        self.damage_dealt = 0.0
        
    def update(self, config: GameConfig, all_ships: List['Ship'], all_cores: List['Core'], 
               map_objects: List['MapObject'], simulator: 'SpaceWarSimulator'):
        """更新舰船状态"""
        if self.health <= 0: 
            return

        self._update_effects()
        self._ai_behavior(all_ships, all_cores)
        self._move(config, simulator)
        self._handle_boundaries()
        self._interact_with_objects(map_objects)
        self._update_retreat_healing(config, simulator)
        self._update_timers()
        
    def _update_effects(self):
        """更新Buff和Debuff效果"""
        self.buffs = [(e, d - 1) for e, d in self.buffs if d > 1]
        self.debuffs = [(e, d - 1) for e, d in self.debuffs if d > 1]
        
    def _ai_behavior(self, all_ships: List['Ship'], all_cores: List['Core']):
        """AI行为逻辑"""
        # 低血量时撤退
        if self.health < self.max_health * 0.25:
            self.state = "retreat"
            self.target = None
            return
            
        # 清除无效目标
        if self.target and self.target.health <= 0:
            self.target = None

        # 寻找最近的敌方舰船
        closest_enemy_ship = self._find_closest_enemy_ship(all_ships)
        if closest_enemy_ship:
            ship, distance = closest_enemy_ship
            if distance <= self.attack_range * 1.3:
                self.target = ship
                self.state = "attack_ship"
                return
                
        # 寻找最近的敌方核心
        closest_enemy_core = self._find_closest_enemy_core(all_cores)
        if closest_enemy_core:
            core, distance = closest_enemy_core
            self.target = core
            self.state = "assault_core"
            return
            
        # 默认巡逻状态
        self.state = "patrol"
        self.target = None
        
    def _find_closest_enemy_ship(self, all_ships: List['Ship']):
        """寻找最近的敌方舰船"""
        closest_ship = None
        closest_distance = float('inf')
        
        for ship in all_ships:
            if ship.faction_id != self.faction_id and ship.health > 0:
                distance = self.pos.distance_to(ship.pos)
                if distance < closest_distance:
                    closest_distance = distance
                    closest_ship = ship
                    
        return (closest_ship, closest_distance) if closest_ship else None
        
    def _find_closest_enemy_core(self, all_cores: List['Core']):
        """寻找最近的敌方核心"""
        closest_core = None
        closest_distance = float('inf')
        
        for core in all_cores:
            if core.faction_id != self.faction_id and core.health > 0:
                distance = self.pos.distance_to(core.pos)
                if distance < closest_distance:
                    closest_distance = distance
                    closest_core = core
                    
        return (closest_core, closest_distance) if closest_core else None
        
    def _move(self, config: GameConfig, simulator: 'SpaceWarSimulator'):
        """移动和转向逻辑"""
        target_pos = self._get_target_position()
        
        self.is_moving = False
        if target_pos:
            self._turn_towards_target(target_pos, config)
            
            if self.pos.distance_to(target_pos) > 15:
                self.is_moving = True
                
            # 计算移动速度（考虑效果修正）
            speed_modifier = self._calculate_speed_modifier()
            self.velocity = Vector2(math.cos(self.angle), math.sin(self.angle)) * self.speed * speed_modifier
        else:
            self.velocity = Vector2(0, 0)
            
        # 更新位置
        if self.is_moving:
            self.pos += self.velocity / 60
        
        # 尝试攻击
        if (self.state in ["attack_ship", "assault_core"]) and self.target and self.attack_cooldown == 0:
            self._attack(self.target, simulator)
            
    def _get_target_position(self):
        """获取目标位置"""
        if (self.state == "attack_ship" or self.state == "assault_core") and self.target:
            return self.target.pos
        elif self.state == "retreat":
            return self.patrol_center
        else:  # patrol
            return self._get_patrol_target()
            
    def _get_patrol_target(self):
        """获取巡逻目标位置"""
        if (self.pos.distance_to(self.patrol_center) > self.patrol_radius or 
            not hasattr(self, 'patrol_target') or 
            self.pos.distance_to(self.patrol_target) < 60):
            
            angle = random.uniform(0, 2 * math.pi)
            self.patrol_target = self.patrol_center + Vector2(
                math.cos(angle), math.sin(angle)
            ) * self.patrol_radius
            
        return self.patrol_target
        
    def _turn_towards_target(self, target_pos: Vector2, config: GameConfig):
        """转向目标位置"""
        direction = target_pos - self.pos
        if direction.magnitude() > 1:
            target_angle = math.atan2(direction.y, direction.x)
            angle_diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
            max_turn_this_frame = config.ship_turn_rate / 60
            turn_amount = max(-max_turn_this_frame, min(max_turn_this_frame, angle_diff))
            self.angle += turn_amount
            self.angle = (self.angle + math.pi) % (2 * math.pi) - math.pi
            
    def _calculate_speed_modifier(self):
        """计算速度修正值"""
        speed_modifier = 1.0
        for effect, _ in self.debuffs:
            speed_modifier *= effect
        for effect, _ in self.buffs:
            speed_modifier *= effect
        return speed_modifier
        
    def _attack(self, target: Union['Ship', 'Core'], simulator: 'SpaceWarSimulator'):
        """执行攻击"""
        if target.health <= 0 or self.pos.distance_to(target.pos) > self.attack_range:
            return
            
        to_target = target.pos - self.pos
        if to_target.magnitude() > 0:
            angle_to_target = math.atan2(to_target.y, to_target.x)
            angle_diff = (angle_to_target - self.angle + math.pi) % (2*math.pi) - math.pi
            
            if abs(angle_diff) <= self.attack_angle / 2:
                damage = self._calculate_attack_damage()
                self._record_damage_stats(damage, simulator)
                self._create_projectile(target, damage, simulator)
                self.attack_cooldown = self.attack_cooldown_max
                
    def _calculate_attack_damage(self):
        """计算攻击伤害"""
        damage = self.attack_damage
        for effect, _ in self.buffs:
            damage *= effect
        return damage
        
    def _record_damage_stats(self, damage: float, simulator: 'SpaceWarSimulator'):
        """记录伤害统计"""
        self.damage_dealt += damage
        
        # 更新阵营统计
        for core in simulator.cores:
            if core.faction_id == self.faction_id and core.health > 0:
                core.total_damage_dealt += damage
                break
                
    def _create_projectile(self, target, damage: float, simulator: 'SpaceWarSimulator'):
        """创建子弹"""
        from entities.projectile import Projectile
        color = FACTION_COLORS[self.faction_id % len(FACTION_COLORS)]
        projectile = Projectile(self.pos, target, damage, color)
        simulator.projectiles.append(projectile)
        
    def _update_retreat_healing(self, config: GameConfig, simulator: 'SpaceWarSimulator'):
        """更新撤退时的治疗效果"""
        if self.state == "retreat":
            self.health = min(self.max_health, self.health + config.ship_retreat_heal_rate / 60)
            self.heal_particle_timer += 1
            if self.heal_particle_timer > 8:
                self.heal_particle_timer = 0
                self._create_heal_effect(simulator)
                
    def _create_heal_effect(self, simulator: 'SpaceWarSimulator'):
        """创建治疗粒子效果"""
        from entities.explosion import Explosion
        particle = Explosion(self.pos, HEAL_GREEN, 2, (1, 3), (10, 20))
        simulator.effects.append(particle)
        
    def _update_timers(self):
        """更新计时器"""
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
            
        if self.damage_flash_timer > 0:
            self.damage_flash_timer -= 1
            
    def _handle_boundaries(self):
        """处理边界限制"""
        self.pos.x = max(20, min(SCREEN_WIDTH - 20, self.pos.x))
        self.pos.y = max(20, min(SCREEN_HEIGHT - 20, self.pos.y))
        
    def _interact_with_objects(self, map_objects: List['MapObject']):
        """与地图物体交互"""
        for obj in map_objects:
            if obj.active and self.pos.distance_to(obj.pos) < obj.size + 15:
                self._apply_object_effect(obj)
                obj.active = False
                return
                
    def _apply_object_effect(self, obj):
        """应用地图物体效果"""
        if obj.type.value == "resource":
            self.health = min(self.health + obj.effect_value, self.max_health)
        elif obj.type.value == "buff":
            self.buffs.append((obj.effect_value, obj.effect_duration))
        elif obj.type.value == "debuff":
            self.debuffs.append((obj.effect_value, obj.effect_duration))
            
    def take_damage(self, damage: float, simulator: 'SpaceWarSimulator'):
        """受到伤害"""
        old_health = self.health
        self.health -= damage
        self.damage_flash_timer = 6
        
        if self.health <= 0 and old_health > 0:
            self.health = 0
            self._record_kill_stats(simulator)
            self._create_destruction_effect(simulator)
            
    def _record_kill_stats(self, simulator: 'SpaceWarSimulator'):
        """记录击杀统计"""
        for core in simulator.cores:
            if core.faction_id == self.faction_id and core.health > 0:
                core.total_kills += 1
                break
                
    def _create_destruction_effect(self, simulator: 'SpaceWarSimulator'):
        """创建摧毁特效"""
        from entities.explosion import Explosion
        color = FACTION_COLORS[self.faction_id % len(FACTION_COLORS)]
        explosion = Explosion(self.pos, color, 80, (2, 6), (30, 60))
        simulator.effects.append(explosion)
        
    def draw(self, screen):
        """绘制舰船"""
        if self.health <= 0:
            return
            
        color = FACTION_COLORS[self.faction_id % len(FACTION_COLORS)]
        body_color = DARK_GRAY
        
        if self.damage_flash_timer > 0:
            body_color, color = WHITE, WHITE
            
        # 绘制引擎尾焰
        if self.is_moving:
            self._draw_engine_flames(screen)
        
        # 绘制舰船主体
        self._draw_ship_body(screen, body_color, color)
        
        # 绘制效果指示器
        self._draw_effect_indicators(screen)
        
        # 绘制血量条
        if self.health < self.max_health:
            self._draw_health_bar(screen)
            
    def _draw_engine_flames(self, screen):
        """绘制引擎尾焰"""
        flame_len = self.length * 1.2 * random.uniform(0.7, 1.3)
        flame_w = self.width * 0.8
        flame_c = self.pos - Vector2(math.cos(self.angle), math.sin(self.angle)) * (self.length / 1.6)
        
        p1 = flame_c + Vector2(math.cos(self.angle+math.pi/2), math.sin(self.angle+math.pi/2)) * flame_w/2
        p2 = flame_c + Vector2(math.cos(self.angle-math.pi/2), math.sin(self.angle-math.pi/2)) * flame_w/2
        flame_tip = flame_c - Vector2(math.cos(self.angle), math.sin(self.angle)) * flame_len
        
        # 外层火焰
        pygame.draw.polygon(screen, ORANGE, [(p1.x, p1.y), (p2.x, p2.y), (flame_tip.x, flame_tip.y)])
        # 内层火焰
        inner_flame_tip = flame_c - Vector2(math.cos(self.angle), math.sin(self.angle)) * flame_len * 0.6
        pygame.draw.polygon(screen, YELLOW, [(p1.x, p1.y), (p2.x, p2.y), (inner_flame_tip.x, inner_flame_tip.y)])
        
    def _draw_ship_body(self, screen, body_color, color):
        """绘制舰船主体"""
        l, w = self.length / 2, self.width / 2
        points = [
            (self.pos.x + l*math.cos(self.angle), self.pos.y + l*math.sin(self.angle)),
            (self.pos.x + w*math.cos(self.angle-math.pi/2), self.pos.y + w*math.sin(self.angle-math.pi/2)),
            (self.pos.x - l*0.6*math.cos(self.angle), self.pos.y - l*0.6*math.sin(self.angle)),
            (self.pos.x + w*math.cos(self.angle+math.pi/2), self.pos.y + w*math.sin(self.angle+math.pi/2))
        ]
        
        # 阴影
        shadow_points = [(p[0] + 1, p[1] + 1) for p in points]
        pygame.draw.polygon(screen, (20, 20, 20), shadow_points)
        
        pygame.draw.polygon(screen, body_color, points)
        pygame.draw.polygon(screen, color, points, 3)
        
    def _draw_effect_indicators(self, screen):
        """绘制效果指示器"""
        if self.buffs:
            buff_surface = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(buff_surface, (0, 255, 0, 150), (4, 4), 4)
            screen.blit(buff_surface, (self.pos.x + 15, self.pos.y - 15))
            
        if self.debuffs:
            debuff_surface = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(debuff_surface, (255, 0, 255, 150), (4, 4), 4)
            screen.blit(debuff_surface, (self.pos.x + 15, self.pos.y - 5))
            
    def _draw_health_bar(self, screen):
        """绘制血量条"""
        bar_w, bar_h = 28, 5
        bar_x, bar_y = self.pos.x - bar_w/2, self.pos.y - 25
        pygame.draw.rect(screen, (60, 0, 0), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2))
        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, bar_w * (self.health / self.max_health), bar_h))