"""太空战争模拟器 - 主程序入口"""
import pygame
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import GameConfig
from game.simulator import SpaceWarSimulator

def main():
    """主函数"""
    pygame.init()
    
    try:
        # 创建游戏配置
        config = GameConfig()
        
        # 创建并运行模拟器
        simulator = SpaceWarSimulator(config)
        simulator.run()
        
    except Exception as e:
        print(f"游戏运行出错: {e}")
        pygame.quit()
        sys.exit(1)
    
    finally:
        pygame.quit()

if __name__ == "__main__":
    main()