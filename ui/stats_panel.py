"""统计面板UI"""
import pygame
import time
from typing import List
from utils.colors import *
from config import SCREEN_WIDTH

class FleetStatsPanel:
    """舰队统计面板"""
    
    def __init__(self, font, small_font):
        self.font = font
        self.small_font = small_font
        self.panel_width = 380
        self.panel_height = 0
        self.visible = True
        
    def draw(self, screen, cores, game_time):
        """绘制统计面板"""
        if not self.visible:
            return
            
        active_cores = [core for core in cores if core.health > 0]
        if not active_cores:
            return
            
        # 计算面板高度
        self.panel_height = 80 + len(active_cores) * 140
        panel_x = SCREEN_WIDTH - self.panel_width - 10
        panel_y = 10
        
        # 绘制主面板背景
        panel_surface = pygame.Surface((self.panel_width, self.panel_height), pygame.SRCALPHA)
        panel_surface.fill(PANEL_BG)
        pygame.draw.rect(panel_surface, PANEL_BORDER, (0, 0, self.panel_width, self.panel_height), 2)
        screen.blit(panel_surface, (panel_x, panel_y))
        
        # 标题
        title_text = self.font.render("舰队实时状态", True, GOLD)
        screen.blit(title_text, (panel_x + 10, panel_y + 10))
        
        # 游戏时间
        minutes = int(game_time // 60)
        seconds = int(game_time % 60)
        time_text = self.small_font.render(f"游戏时间: {minutes:02d}:{seconds:02d}", True, WHITE)
        screen.blit(time_text, (panel_x + 10, panel_y + 45))
        
        # 各阵营详细信息
        y_offset = 75
        for core in sorted(active_cores, key=lambda c: c.health, reverse=True):
            self._draw_faction_stats(screen, core, panel_x + 10, panel_y + y_offset)
            y_offset += 140
            
    def _draw_faction_stats(self, screen, core, x, y):
        """绘制单个阵营的统计信息"""
        color = FACTION_COLORS[core.faction_id % len(FACTION_COLORS)]
        
        # 阵营标题
        faction_text = self.small_font.render(f"阵营 {core.faction_id + 1}", True, color)
        screen.blit(faction_text, (x, y))
        
        # 核心状态
        health_pct = (core.health / core.max_health) * 100
        health_text = self.small_font.render(f"核心血量: {int(core.health)}/{int(core.max_health)} ({health_pct:.1f}%)", True, WHITE)
        screen.blit(health_text, (x, y + 20))
        
        # 血量条
        bar_width = 200
        bar_height = 8
        pygame.draw.rect(screen, (60, 0, 0), (x, y + 40, bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, (x, y + 40, bar_width * (core.health / core.max_health), bar_height))
        
        # 护盾条
        pygame.draw.rect(screen, (20, 20, 60), (x, y + 50, bar_width, 4))
        pygame.draw.rect(screen, (100, 200, 255), (x, y + 50, bar_width * (core.shield_energy / core.max_shield), 4))
        
        # 舰队信息
        alive_ships = len([ship for ship in core.ships if ship.health > 0])
        fleet_text = self.small_font.render(f"舰队规模: {alive_ships}/{core.max_ships}", True, WHITE)
        screen.blit(fleet_text, (x, y + 58))
        
        # 资源信息
        resource_text = self.small_font.render(f"资源: {int(core.resources)}", True, YELLOW)
        screen.blit(resource_text, (x, y + 76))
        
        # 战斗统计
        stats_text = self.small_font.render(f"击杀: {core.total_kills}", True, RED)
        screen.blit(stats_text, (x, y + 94))
        
        damage_text = self.small_font.render(f"输出伤害: {int(core.total_damage_dealt)}", True, ORANGE)
        screen.blit(damage_text, (x, y + 112))
        
        # 舰队状态分布
        if alive_ships > 0:
            patrol_count = len([s for s in core.ships if s.state == "patrol" and s.health > 0])
            attack_count = len([s for s in core.ships if s.state == "attack_ship" and s.health > 0])
            assault_count = len([s for s in core.ships if s.state == "assault_core" and s.health > 0])
            retreat_count = len([s for s in core.ships if s.state == "retreat" and s.health > 0])
            
            status_text = f"巡逻:{patrol_count} 攻击:{attack_count} 突击:{assault_count} 撤退:{retreat_count}"
            status_surface = self.small_font.render(status_text, True, LIGHT_GRAY)
            screen.blit(status_surface, (x, y + 130))