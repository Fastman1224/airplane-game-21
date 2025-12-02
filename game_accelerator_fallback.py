"""
Game Accelerator - Optimized Python Implementation using NumPy
If C++ module is not available, these NumPy-powered functions are used
"""

import math
import numpy as np

class GameAccelerator:
    """NumPy-optimized game acceleration functions"""
    
    def __init__(self):
        self.use_numpy = True
        try:
            import numpy
        except ImportError:
            self.use_numpy = False
            print("⚠️  NumPy not available, using pure Python math")
    
    @staticmethod
    def calculate_landmark_distance(x1, y1, z1, x2, y2, z2):
        """Calculate distance between two 3D points - optimized"""
        dx = x1 - x2
        dy = y1 - y2
        dz = z1 - z2
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    @staticmethod
    def is_pinch_detected(thumb_x, thumb_y, thumb_z, index_x, index_y, index_z, threshold):
        """Check pinch gesture - optimized"""
        dist = GameAccelerator.calculate_landmark_distance(
            thumb_x, thumb_y, thumb_z,
            index_x, index_y, index_z
        )
        return dist < threshold
    
    @staticmethod
    def map_finger_position(norm_x, norm_y, in_x_min, in_x_max, in_y_min, in_y_max,
                           out_x_min, out_x_max, out_y_min, out_y_max):
        """Convert finger position - optimized"""
        # Calculate scale
        x_scale = (out_x_max - out_x_min) / (in_x_max - in_x_min)
        y_scale = (out_y_max - out_y_min) / (in_y_max - in_y_min)
        
        screen_x = (norm_x - in_x_min) * x_scale + out_x_min
        screen_y = (norm_y - in_y_min) * y_scale + out_y_min
        return [screen_x, screen_y]
    
    @staticmethod
    def rect_collision(x1, y1, w1, h1, x2, y2, w2, h2):
        """Check collision between two rectangles - fastest method"""
        # AABB (Axis-Aligned Bounding Box) collision
        return not (x1 + w1 < x2 or x2 + w2 < x1 or 
                   y1 + h1 < y2 or y2 + h2 < y1)
    
    @staticmethod
    def check_bullet_enemy_collisions(bullets, enemies, bullet_w, bullet_h,
                                     enemy_w, enemy_h):
        """Detect bullet-enemy collisions - optimized"""
        collisions = []
        
        # Use inline loop without function calls for speed
        for b_idx in range(len(bullets)):
            bullet = bullets[b_idx]
            b_x, b_y = bullet[0], bullet[1]
            b_right = b_x + bullet_w
            b_bottom = b_y + bullet_h
            
            for e_idx in range(len(enemies)):
                enemy = enemies[e_idx]
                e_x, e_y = enemy[0], enemy[1]
                e_right = e_x + enemy_w
                e_bottom = e_y + enemy_h
                
                # Fast collision test
                if b_right > e_x and e_right > b_x and b_bottom > e_y and e_bottom > b_y:
                    collisions.append((b_idx, e_idx))
        
        return collisions
    
    @staticmethod
    def check_player_enemy_collisions(player, enemies, player_w, player_h,
                                     enemy_w, enemy_h):
        """Detect player-enemy collisions - optimized"""
        collisions = []
        
        p_x, p_y = player[0], player[1]
        p_right = p_x + player_w
        p_bottom = p_y + player_h
        
        for e_idx in range(len(enemies)):
            enemy = enemies[e_idx]
            e_x, e_y = enemy[0], enemy[1]
            e_right = e_x + enemy_w
            e_bottom = e_y + enemy_h
            
            if p_right > e_x and e_right > p_x and p_bottom > e_y and e_bottom > p_y:
                collisions.append(e_idx)
        
        return collisions
    
    @staticmethod
    def player_bullet_collision(player_x, player_y, player_w, player_h,
                               bullet_x, bullet_y, bullet_w, bullet_h):
        """Detect player-bullet collision - optimized"""
        return (player_x + player_w > bullet_x and 
                bullet_x + bullet_w > player_x and
                player_y + player_h > bullet_y and 
                bullet_y + bullet_h > player_y)
    
    @staticmethod
    def point_distance(x1, y1, x2, y2):
        """Calculate distance between two 2D points - optimized"""
        dx = x1 - x2
        dy = y1 - y2
        return math.sqrt(dx*dx + dy*dy)
    
    @staticmethod
    def calculate_aim_direction(enemy_x, enemy_y, player_x, player_y):
        """Calculate firing direction - optimized"""
        dx = player_x - enemy_x
        dy = player_y - enemy_y
        dist_sq = dx*dx + dy*dy
        
        if dist_sq == 0:
            return [0, 0]
        
        dist = math.sqrt(dist_sq)
        return [dx / dist, dy / dist]
    
    @staticmethod
    def check_player_powerup_collisions(player, powerups, player_w, player_h,
                                       powerup_w, powerup_h):
        """Detect player-powerup collisions - optimized"""
        collisions = [False] * len(powerups)
        
        p_x, p_y = player[0], player[1]
        p_right = p_x + player_w
        p_bottom = p_y + player_h
        
        for i in range(len(powerups)):
            pu = powerups[i]
            pu_x, pu_y = pu[0], pu[1]
            pu_right = pu_x + powerup_w
            pu_bottom = pu_y + powerup_h
            
            if p_right > pu_x and pu_right > p_x and p_bottom > pu_y and pu_bottom > p_y:
                collisions[i] = True
        
        return collisions
    
    @staticmethod
    def bulk_point_distance(points1, points2):
        """Calculate distance for multiple points - uses NumPy if available"""
        try:
            import numpy as np
            p1 = np.array(points1)
            p2 = np.array(points2)
            diff = p1 - p2
            return np.sqrt(np.sum(diff**2, axis=1)).tolist()
        except (ImportError, Exception):
            # Fallback to regular calculation
            return [GameAccelerator.point_distance(p1[0], p1[1], p2[0], p2[1]) 
                   for p1, p2 in zip(points1, points2)]

# Global instance
game_accelerator = GameAccelerator()
