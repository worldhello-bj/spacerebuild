"""游戏模拟器主逻辑"""
import pygame
import random
import math
import time
from typing import List

from config import GameConfig, ObjectType, SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from utils.vector2 import Vector2
from utils.colors import *
from entities import Core, Ship, Projectile, Explosion, MapObject
from ui.stats_panel import FleetStatsPanel

class SpaceWarSimulator:
    """太空战争模拟器主类"""
    
    def __init__(self, config: GameConfig = None):
        self.config = config or GameConfig()
        self._init_pygame()
        self._init_fonts()
        self._init_game_state()
        self._init_ui()
        self.initialize_game()
        
    def _init_pygame(self):
        """初始化Pygame"""
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("太空战争模拟器 - 增强版")
        self.clock = pygame.time.Clock()
        
    def _init_fonts(self):
        """初始化字体"""
        try:
            self.font = pygame.font.Font("msyh.ttf", 28)
            self.small_font = pygame.font.Font("msyh.ttf", 18)
        except FileNotFoundError:
            self.font = pygame.font.Font(None, 28)
            self.small_font = pygame.font.Font(None, 18)
            
    def _init_game_state(self):
        """初始化游戏状态"""
        self.paused = False
        self.show_stats = True
        self.screen_shake = 0
        self.game_start_time = time.time()
        
    def _init_ui(self):
        """初始化UI组件"""
        self.stats_panel = FleetStatsPanel(self.font, self.small_font)
        
    def initialize_game(self):
        """初始化游戏世界"""
        self._reset_game_objects()
        self._create_starfield()
        self._create_faction_cores()
        self._create_map_objects()
        self.game_start_time = time.time()
        
    def _reset_game_objects(self):
        """重置游戏对象"""
        self.cores: List[Core] = []
        self.map_objects: List[MapObject] = []
        self.projectiles: List[Projectile] = []
        self.effects: List[Explosion] = []
        
    def _create_starfield(self):
        """创建星空背景"""
        self.stars = []
        for _ in range(200):
            star_size = random.uniform(0.5, 2.5)
            star_brightness = random.uniform(0.3, 1.0)
            self.stars.append([
                (random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)), 
                star_size, 
                star_brightness,
                random.uniform(0.2, 1.5)  # 移动速度
            ])
            
    def _create_faction_cores(self):
        """创建阵营核心"""
        for i in range(self.config.num_factions):
            attempts = 0
            while attempts < 100:
                pos = Vector2(
                    random.randint(250, SCREEN_WIDTH - 250),
                    random.randint(250, SCREEN_HEIGHT - 250)
                )
                if all(pos.distance_to(c.pos) > 350 for c in self.cores):
                    self.cores.append(Core(pos, i, self.config))
                    break
                attempts += 1
                
    def _create_map_objects(self):
        """创建地图物体"""
        obj_types = [ObjectType.OBSTACLE, ObjectType.RESOURCE, ObjectType.BUFF, ObjectType.DEBUFF]
        weights = [0.65, 0.18, 0.10, 0.07]
        
        for _ in range(self.config.map_objects_count):
            obj_type = random.choices(obj_types, weights=weights, k=1)[0]
            attempts = 0
            while attempts < 50:
                pos = Vector2(
                    random.randint(120, SCREEN_WIDTH - 120),
                    random.randint(120, SCREEN_HEIGHT - 120)
                )
                if (all(pos.distance_to(c.pos) > 180 for c in self.cores) and 
                    all(pos.distance_to(o.pos) > 120 for o in self.map_objects)):
                    size_range = getattr(self.config, f"{obj_type.value}_size_range")
                    obj = MapObject(pos, random.uniform(*size_range), obj_type)
                    self.map_objects.append(obj)
                    break
                attempts += 1
                
    def update(self):
        """更新游戏状态"""
        if self.paused:
            return
            
        self._update_map_objects()
        self._update_entities()
        self._update_effects()
        self._cleanup_objects()
        self._handle_object_respawn()
        self._update_screen_shake()
        
    def _update_map_objects(self):
        """更新地图物体"""
        for obj in self.map_objects:
            if obj.active:
                obj.update()
                
    def _update_entities(self):
        """更新游戏实体"""
        active_cores = [core for core in self.cores if core.health > 0]
        all_ships = [ship for core in active_cores for ship in core.ships]
        
        # 更新核心
        for core in active_cores:
            if core.health <= 0:
                continue
            core.update(self.config, self.map_objects, active_cores)
            core.ships = [ship for ship in core.ships if ship.health > 0]
            
            # 更新舰船
            for ship in core.ships: 
                ship.update(self.config, all_ships, active_cores, self.map_objects, self)
                
        # 更新子弹
        for proj in self.projectiles:
            proj.update(self)
            
    def _update_effects(self):
        """更新特效"""
        for effect in self.effects:
            effect.update()
            
    def _cleanup_objects(self):
        """清理无效对象"""
        self.projectiles = [p for p in self.projectiles if p.lifetime > 0]
        self.effects = [e for e in self.effects if hasattr(e, 'particles') and e.particles]
        self.cores = [core for core in self.cores if core.health > 0]
        
    def _handle_object_respawn(self):
        """处理地图物体重生"""
        inactive_objects = [o for o in self.map_objects if not o.active]
        if len(inactive_objects) > 0 and random.random() < 0.002:
            obj = random.choice(inactive_objects)
            obj.active = True
            
    def _update_screen_shake(self):
        """更新屏幕震动"""
        if self.screen_shake > 0:
            self.screen_shake -= 1
            
    def draw(self):
        """绘制游戏画面"""
        shake_x, shake_y = self._calculate_screen_shake()
        
        self.screen.fill((5, 5, 15))  # 深空背景
        temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        self._draw_starfield(temp_surface)
        self._draw_map_objects(temp_surface)
        self._draw_entities(temp_surface)
        self._draw_projectiles(temp_surface)
        self._draw_effects(temp_surface)
        
        # 应用屏幕震动
        self.screen.blit(temp_surface, (shake_x, shake_y))
        
        # 绘制UI
        self._draw_ui()
        pygame.display.flip()
        
    def _calculate_screen_shake(self):
        """计算屏幕震动偏移"""
        shake_x = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        shake_y = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        return shake_x, shake_y
        
    def _draw_starfield(self, surface):
        """绘制星空背景"""
        for star in self.stars:
            star[0] = ((star[0][0] - star[3]), star[0][1])
            if star[0][0] < 0:
                star[0] = (SCREEN_WIDTH + random.randint(0, 100), random.randint(0, SCREEN_HEIGHT))
            
            # 星星闪烁效果
            brightness = star[2] * (0.8 + 0.2 * math.sin(pygame.time.get_ticks() * 0.001 + star[0][0] * 0.01))
            star_color = (int(255 * brightness), int(255 * brightness), int(255 * brightness))
            star_size = int(star[1] * (0.8 + 0.4 * brightness))
            
            if star_size > 0:
                pygame.draw.circle(surface, star_color, star[0], star_size)
                
    def _draw_map_objects(self, surface):
        """绘制地图物体"""
        for obj in self.map_objects:
            if obj.active:
                obj.draw(surface)
                
    def _draw_entities(self, surface):
        """绘制游戏实体"""
        # 按Y坐标排序以实现深度效果
        all_game_objects = self.cores + [ship for core in self.cores for ship in core.ships]
        all_game_objects.sort(key=lambda obj: obj.pos.y)

        for obj in all_game_objects:
            obj.draw(surface)
            
    def _draw_projectiles(self, surface):
        """绘制子弹"""
        for proj in self.projectiles:
            proj.draw(surface)
            
    def _draw_effects(self, surface):
        """绘制特效"""
        for effect in self.effects:
            effect.draw(surface)
            
    def _draw_ui(self):
        """绘制用户界面"""
        self._draw_stats_panel()
        self._draw_control_panel()
        self._draw_game_status()
        
    def _draw_stats_panel(self):
        """绘制统计面板"""
        if self.show_stats:
            game_time = time.time() - self.game_start_time
            self.stats_panel.draw(self.screen, self.cores, game_time)
            
    def _draw_control_panel(self):
        """绘制控制面板"""
        controls_width, controls_height = 200, 120
        controls_surface = pygame.Surface((controls_width, controls_height), pygame.SRCALPHA)
        controls_surface.fill(PANEL_BG)
        pygame.draw.rect(controls_surface, PANEL_BORDER, (0, 0, controls_width, controls_height), 2)
        self.screen.blit(controls_surface, (10, SCREEN_HEIGHT - controls_height - 10))
        
        controls_text = [
            "控制说明:",
            "空格: 暂停/继续",
            "Tab: 显示/隐藏面板", 
            "R: 重新开始",
            "ESC: 退出游戏"
        ]
        
        for i, text in enumerate(controls_text):
            color = GOLD if i == 0 else WHITE
            text_surface = self.small_font.render(text, True, color)
            self.screen.blit(text_surface, (20, SCREEN_HEIGHT - controls_height + 10 + i * 20))
            
    def _draw_game_status(self):
        """绘制游戏状态"""
        if len(self.cores) <= 1:
            self._draw_game_end_status()
        elif self.paused:
            self._draw_pause_status()
            
    def _draw_game_end_status(self):
        """绘制游戏结束状态"""
        if len(self.cores) == 1:
            winner_text = f"阵营 {self.cores[0].faction_id + 1} 获胜!"
            winner_color = FACTION_COLORS[self.cores[0].faction_id % len(FACTION_COLORS)]
        else:
            winner_text = "平局!"
            winner_color = WHITE
            
        self._draw_centered_text(winner_text, winner_color, SCREEN_HEIGHT//2 - 50)
        self._draw_centered_text("按 R 重新开始", WHITE, SCREEN_HEIGHT//2, font=self.small_font)
        
    def _draw_pause_status(self):
        """绘制暂停状态"""
        self._draw_centered_text("游戏暂停", YELLOW, 50)
        
    def _draw_centered_text(self, text: str, color, y_pos: int, font=None):
        """绘制居中文本"""
        if font is None:
            font = self.font
            
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH//2, y_pos))
        
        # 文本背景
        bg_surface = pygame.Surface((text_rect.width + 40, text_rect.height + 20), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 180))
        self.screen.blit(bg_surface, (text_rect.x - 20, text_rect.y - 10))
        
        self.screen.blit(text_surface, text_rect)
        
    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if not self._handle_key_press(event.key):
                    return False
        return True
        
    def _handle_key_press(self, key):
        """处理按键事件"""
        if key == pygame.K_SPACE:
            self.paused = not self.paused
        elif key == pygame.K_TAB:
            self.stats_panel.visible = not self.stats_panel.visible
        elif key == pygame.K_r:
            self.initialize_game()
        elif key == pygame.K_ESCAPE:
            return False
        return True
        
    def run(self):
        """运行游戏主循环"""
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()