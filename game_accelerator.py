"""
Game Accelerator - Pure Python Implementation
Provides fast collision detection and game calculations
"""

import math
from typing import List, Tuple, Dict

# Collision detection functions

def check_bullet_enemy_collisions(
    bullets: List[List[float]],
    enemies: List[List[float]],
    bullet_w: float,
    bullet_h: float,
    enemy_w: float,
    enemy_h: float
) -> List[Tuple[int, int]]:
    """Fast bullet-enemy collision detection"""
    collisions = []
    
    for b_idx, bullet in enumerate(bullets):
        bullet_x, bullet_y = bullet[0], bullet[1]
        bullet_rect = (bullet_x, bullet_y, bullet_w, bullet_h)
        
        for e_idx, enemy in enumerate(enemies):
            enemy_x, enemy_y = enemy[0], enemy[1]
            enemy_rect = (enemy_x, enemy_y, enemy_w, enemy_h)
            
            if _rects_collide(bullet_rect, enemy_rect):
                collisions.append((b_idx, e_idx))
    
    return collisions


def check_player_enemy_collisions(
    player: List[float],
    enemies: List[List[float]],
    player_w: float,
    player_h: float,
    enemy_w: float,
    enemy_h: float
) -> List[int]:
    """Fast player-enemy collision detection"""
    collisions = []
    player_x, player_y = player[0], player[1]
    player_rect = (player_x, player_y, player_w, player_h)
    
    for e_idx, enemy in enumerate(enemies):
        enemy_x, enemy_y = enemy[0], enemy[1]
        enemy_rect = (enemy_x, enemy_y, enemy_w, enemy_h)
        
        if _rects_collide(player_rect, enemy_rect):
            collisions.append(e_idx)
    
    return collisions


def calculate_landmark_distance(
    x1: float, y1: float, z1: float,
    x2: float, y2: float, z2: float
) -> float:
    """Calculate distance between two 3D points"""
    dx = x1 - x2
    dy = y1 - y2
    dz = z1 - z2
    return math.sqrt(dx*dx + dy*dy + dz*dz)


def is_pinch_detected(
    thumb_x: float, thumb_y: float, thumb_z: float,
    index_x: float, index_y: float, index_z: float,
    threshold: float
) -> bool:
    """Check if pinch gesture is detected"""
    dist = calculate_landmark_distance(
        thumb_x, thumb_y, thumb_z,
        index_x, index_y, index_z
    )
    return dist < threshold


def map_finger_position(
    norm_x: float, norm_y: float,
    in_x_min: float, in_x_max: float, in_y_min: float, in_y_max: float,
    out_x_min: float, out_x_max: float, out_y_min: float, out_y_max: float
) -> List[float]:
    """Map normalized finger position to screen coordinates"""
    screen_x = (norm_x - in_x_min) * (out_x_max - out_x_min) / (in_x_max - in_x_min) + out_x_min
    screen_y = (norm_y - in_y_min) * (out_y_max - out_y_min) / (in_y_max - in_y_min) + out_y_min
    return [screen_x, screen_y]


def update_enemy_positions(
    enemies: List[List[float]],
    enemy_speeds: List[float],
    screen_width: int,
    screen_height: int
) -> List[List[float]]:
    """Update all enemy positions"""
    result = [enemy[:] for enemy in enemies]  # Deep copy
    
    for i, enemy in enumerate(result):
        enemy[0] += enemy[4]  # speed_x
        enemy[1] += enemy_speeds[i]  # speed_y
        
        # Boundary check
        if enemy[0] < 0:
            enemy[0] = 0
        if enemy[0] > screen_width:
            enemy[0] = screen_width
    
    return result


def calculate_aim_direction(
    enemy_x: float, enemy_y: float,
    player_x: float, player_y: float
) -> List[float]:
    """Calculate aim direction for enemy shots"""
    dx = player_x - enemy_x
    dy = player_y - enemy_y
    dist = math.sqrt(dx*dx + dy*dy)
    
    if dist == 0:
        return [0, 0]
    
    return [dx / dist, dy / dist]


def bullet_boss_collision(
    bullet_x: float, bullet_y: float, bullet_w: float, bullet_h: float,
    boss_x: float, boss_y: float, boss_w: float, boss_h: float
) -> bool:
    """Check bullet-boss collision"""
    bullet_rect = (bullet_x, bullet_y, bullet_w, bullet_h)
    boss_rect = (boss_x, boss_y, boss_w, boss_h)
    return _rects_collide(bullet_rect, boss_rect)


def player_bullet_collision(
    player_x: float, player_y: float, player_w: float, player_h: float,
    bullet_x: float, bullet_y: float, bullet_w: float, bullet_h: float
) -> bool:
    """Check player-bullet collision"""
    player_rect = (player_x, player_y, player_w, player_h)
    bullet_rect = (bullet_x, bullet_y, bullet_w, bullet_h)
    return _rects_collide(player_rect, bullet_rect)


def point_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate distance between two 2D points"""
    dx = x1 - x2
    dy = y1 - y2
    return math.sqrt(dx*dx + dy*dy)


def check_player_powerup_collisions(
    player: List[float],
    powerups: List[List[float]],
    player_w: float,
    player_h: float,
    powerup_w: float,
    powerup_h: float
) -> List[bool]:
    """Check player-powerup collisions"""
    collisions = [False] * len(powerups)
    player_x, player_y = player[0], player[1]
    player_rect = (player_x, player_y, player_w, player_h)
    
    for i, powerup in enumerate(powerups):
        powerup_x, powerup_y = powerup[0], powerup[1]
        powerup_rect = (powerup_x, powerup_y, powerup_w, powerup_h)
        
        if _rects_collide(player_rect, powerup_rect):
            collisions[i] = True
    
    return collisions


# Helper functions

def _rects_collide(rect1: Tuple[float, float, float, float], 
                   rect2: Tuple[float, float, float, float]) -> bool:
    """Check if two rectangles collide (AABB collision detection)"""
    x1, y1, w1, h1 = rect1
    x2, y2, w2, h2 = rect2
    
    return not (x1 + w1 < x2 or x2 + w2 < x1 or
                y1 + h1 < y2 or y2 + h2 < y1)
