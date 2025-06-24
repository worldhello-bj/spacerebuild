"""2D向量数学工具"""
import math

class Vector2:
    """2D向量类"""
    
    def __init__(self, x: float = 0, y: float = 0):
        self.x, self.y = x, y
        
    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)
        
    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)
        
    def __mul__(self, scalar):
        return Vector2(self.x * scalar, self.y * scalar)
        
    def __truediv__(self, scalar):
        return Vector2(self.x / scalar, self.y / scalar)
        
    def magnitude(self):
        return math.sqrt(self.x * self.x + self.y * self.y)
        
    def normalized(self):
        mag = self.magnitude()
        return Vector2(0, 0) if mag == 0 else Vector2(self.x / mag, self.y / mag)
        
    def distance_to(self, other):
        return (self - other).magnitude()