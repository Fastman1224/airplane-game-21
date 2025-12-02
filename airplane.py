import cv2
import mediapipe as mp
import pygame
import random
import math
import time
import os

# Attempt to import C++ acceleration module
try:
    import game_accelerator
    ENABLE_CPP_ACCELERATION = True
    print("✅ C++ acceleration enabled!")
except ImportError:
    try:
        from game_accelerator_fallback import game_accelerator
        ENABLE_CPP_ACCELERATION = True
        print("⚠️  Using Python fallback for acceleration")
    except ImportError:
        ENABLE_CPP_ACCELERATION = False
        print("⚠️  No acceleration available. Running pure Python.")

os.environ["QT_QPA_PLATFORM"] = "xcb"

mp_hands = mp.solutions.hands
hands_detector = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 900, 700
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("AI Enhanced Finger Shooter - 8D Movement")
clock = pygame.time.Clock()
title_font = pygame.font.SysFont("Arial", 70, bold=True)
main_font = pygame.font.SysFont("Arial", 45)
hud_font = pygame.font.SysFont("Consolas", 35)
small_hud_font = pygame.font.SysFont("Consolas", 22)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
DEEP_RED = (180, 0, 0)
ORANGE = (255, 165, 0)
PLAYER_SHIP_COLOR = (0, 200, 255)
PLAYER_BULLET_COLOR = (255, 255, 0)
ENEMY_NORMAL_COLOR = (130, 130, 130)
ENEMY_CHASER_COLOR = (220, 50, 220)
ENEMY_SHOOTER_COLOR = (255, 100, 0)
ENEMY_DODGER_COLOR = (0, 200, 100)
ENEMY_BULLET_COLOR = (255, 60, 60)
BOSS_COLOR = (60, 60, 60)
BOSS_SPECIAL_ATTACK_COLOR = (255,0,255)
BOSS_HEALTH_BAR_COLOR = (0, 255, 0)
BOSS_HEALTH_BAR_BG_COLOR = (40, 40, 40)
POWER_UP_SHIELD_COLOR = (0, 100, 255)
POWER_UP_MULTI_SHOT_COLOR = (255,0,255)
STAR_COLOR = (200, 200, 200)
EXPLOSION_COLORS_DEFAULT = [(255,0,0), (255,165,0), (255,255,0)]
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
DEBUG_TEXT_COLOR = (200, 200, 0)

GAME_STATE_INSTRUCTIONS = "instructions"
GAME_STATE_PLAYING = "playing"
GAME_STATE_LEVEL_UP = "level_up"
GAME_STATE_BOSS_FIGHT = "boss_fight"
GAME_STATE_GAME_OVER = "game_over"
GAME_STATE_PAUSED_NO_HAND = "paused_no_hand"
current_game_state = GAME_STATE_INSTRUCTIONS

player_width = 55
player_height = 45
player_rect = pygame.Rect(SCREEN_WIDTH // 2 - player_width // 2, SCREEN_HEIGHT * 0.75 - player_height // 2, player_width, player_height) # Initial Y
player_lives_start = 3
player_invincibility_duration_ms = 2500
player_invincible_until_ms = 0
player_shield_active = False
player_shield_duration_ms = 7000
player_shield_end_time_ms = 0
player_multi_shot_active = False
player_multi_shot_duration_ms = 8000
player_multi_shot_end_time_ms = 0

PLAYER_PLAYABLE_Y_MIN = SCREEN_HEIGHT // 3
PLAYER_PLAYABLE_Y_MAX = SCREEN_HEIGHT - player_height // 2


current_level = 1
score_to_next_level_base = 400
score_for_next_level = score_to_next_level_base
level_up_message_duration_ms = 2500
level_up_message_end_time_ms = 0
boss_fight_trigger_level = 3
boss_active = False

base_enemy_speed_y = 2.2
enemy_spawn_rate_initial = 65
enemy_spawn_rate_current = enemy_spawn_rate_initial
enemy_width_std = 45
enemy_height_std = 35
all_enemies_list = []
enemy_bullets_master_list = []
enemy_bullet_base_speed = 4.5

player_bullets_list = []
player_bullet_speed = 15
player_bullet_width = 7
player_bullet_height = 22
player_base_shoot_cooldown_ms = 280
player_current_shoot_cooldown_ms = player_base_shoot_cooldown_ms
player_last_shot_time_ms = 0

boss_main_rect = pygame.Rect(SCREEN_WIDTH // 2 - 75, 40, 150, 120)
boss_max_health_base = 40
boss_current_health = boss_max_health_base
boss_speed_x_current = 2.5
boss_base_shoot_cooldown_ms = 700
boss_last_shot_time_ms = 0
boss_bullets_master_list = []
boss_current_phase = 1
boss_phase_change_health_threshold_factor = 0.5
boss_state = "ENTERING"
boss_state_timer = 0

power_ups_list = []
POWER_UP_TYPE_SHIELD = "shield"
POWER_UP_TYPE_MULTI_SHOT = "multi_shot"
power_up_base_drop_chance = 0.08

score = 0
show_debug_info = False

webcam_capture = cv2.VideoCapture(0)
if not webcam_capture.isOpened():
    pygame.quit()
    exit()

INDEX_FINGER_TIP_ID = 8
THUMB_TIP_ID = 4
PINCH_GESTURE_THRESHOLD = 0.040

stars_list = []
NUM_STARS_BG = 200
for _ in range(NUM_STARS_BG):
    stars_list.append([random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), random.randint(1, 4)])

class Explosion:
    def __init__(self, center_pos, num_particles=20, max_radius=35, duration=450, colors=None, particle_speed_range=(1,3.5)):
        self.center_pos = center_pos
        self.creation_time = pygame.time.get_ticks()
        self.particles = []
        self.colors_to_use = colors if colors else EXPLOSION_COLORS_DEFAULT
        self.particle_min_speed, self.particle_max_speed = particle_speed_range
        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(self.particle_min_speed, self.particle_max_speed)
            radius = random.uniform(max_radius * 0.08, max_radius * 0.18)
            color = random.choice(self.colors_to_use)
            self.particles.append({
                'x': center_pos[0], 'y': center_pos[1],
                'vx': math.cos(angle) * speed, 'vy': math.sin(angle) * speed,
                'radius': radius, 'color': color, 'alpha': 255, 'start_radius': radius
            })
        self.duration = duration

    def update(self):
        current_time_ms = pygame.time.get_ticks()
        age_ms = current_time_ms - self.creation_time
        if age_ms > self.duration: return False
        for p_data in self.particles:
            p_data['x'] += p_data['vx']
            p_data['y'] += p_data['vy']
            p_data['alpha'] = max(0, 255 - (age_ms / self.duration) * 255)
            p_data['radius'] = p_data['start_radius'] * (1 - age_ms / self.duration)
        return True

    def draw(self, surface_to_draw_on):
        for p_data in self.particles:
            if p_data['alpha'] > 0 and p_data['radius'] > 0.5:
                particle_surf = pygame.Surface((int(p_data['radius']*2), int(p_data['radius']*2)), pygame.SRCALPHA)
                pygame.draw.circle(particle_surf, (*p_data['color'], int(p_data['alpha'])), (int(p_data['radius']), int(p_data['radius'])), int(p_data['radius']))
                surface_to_draw_on.blit(particle_surf, (int(p_data['x'] - p_data['radius']), int(p_data['y'] - p_data['radius'])))
active_explosions_list = []

class EnemyAI:
    def __init__(self, x_pos, y_pos, enemy_variant, player_lvl):
        self.variant = enemy_variant
        self.player_level_modifier = player_lvl
        self.rect = pygame.Rect(x_pos, y_pos, enemy_width_std, enemy_height_std)
        self.current_speed_y = base_enemy_speed_y + (self.player_level_modifier - 1) * 0.25
        self.current_speed_x = 0
        self.ai_state = 'ENTERING'
        self.ai_state_timer_frames = 0
        self.shoot_action_cooldown_frames = 120 
        self.shoot_action_timer_frames = random.randint(0, self.shoot_action_cooldown_frames // 2)
        self.dodge_timer_frames = 0
        self.dodge_direction = 1  # initialize dodge_direction
        self.patrol_direction = 1 if random.random() < 0.5 else -1
        self.patrol_range_x = (self.rect.x - 50, self.rect.x + 50)
        self.dodge_cooldown_frames = 45  # default for dodging
        self.dodge_duration_frames = 15  # added default dodge duration to fix attribute error

        if self.variant == 'chaser':
            self.health_points = int((2 + self.player_level_modifier // 2) * 1.5)  # increased health
            self.color_fill = ENEMY_CHASER_COLOR
            self.chase_aggressiveness = 0.45 * 1.2 + (self.player_level_modifier - 1) * 0.02  # increased aggressiveness
        elif self.variant == 'shooter':
            self.health_points = int((1 + self.player_level_modifier // 3) * 1.5)  # increased health
            self.color_fill = ENEMY_SHOOTER_COLOR
            self.shoot_action_cooldown_frames = max(20, int((100 - (self.player_level_modifier - 1) * 7) * 0.8))  # faster shooting
        elif self.variant == 'dodger':
            self.health_points = int(1 * 1.5)  # increased health
            self.color_fill = ENEMY_DODGER_COLOR
            self.current_speed_y *= 1.2 * 1.1  # further increase speed
            self.dodge_cooldown_frames = 35  # reduced cooldown for more frequent dodging
            self.dodge_duration_frames = 15
        else:
            self.color_fill = ENEMY_NORMAL_COLOR
            self.health_points = int((1 + self.player_level_modifier // 4) * 1.5)  # increased health

    def update_behavior(self, player_main_rect, player_bullet_list_ref, all_other_enemies_list_ref):
        global enemy_bullets_master_list
        self.ai_state_timer_frames += 1
        self.current_speed_x = 0
        # New: For normal enemies, dodge incoming player bullets to leave gap when player shoots
        if self.variant not in ['dodger', 'chaser', 'shooter'] and self.dodge_timer_frames <= 0:
            for p_bullet in player_bullet_list_ref:
                detection_rect = self.rect.inflate(self.rect.width, self.rect.height)
                if detection_rect.colliderect(p_bullet):
                    self.ai_state = 'DODGING'
                    self.ai_state_timer_frames = 0
                    self.dodge_timer_frames = self.dodge_cooldown_frames + self.dodge_duration_frames
                    self.dodge_direction = 1 if p_bullet.centerx < self.rect.centerx else -1
                    break

        # Existing dodge for chaser/shooter remains
        if self.variant in ['chaser', 'shooter'] and self.dodge_timer_frames <= 0:
            for p_bullet in player_bullet_list_ref:
                detection_rect = self.rect.inflate(self.rect.width * 1.0, self.rect.height * 1.3)
                if detection_rect.colliderect(p_bullet):
                    self.ai_state = 'DODGING'
                    self.ai_state_timer_frames = 0
                    self.dodge_timer_frames = self.dodge_cooldown_frames + self.dodge_duration_frames
                    self.dodge_direction = 1 if p_bullet.centerx < self.rect.centerx else -1
                    break

        if self.ai_state == 'ENTERING':
            self.rect.y += self.current_speed_y * 0.6
            if self.rect.top > random.randint(30, 70):
                self.ai_state = 'PATROLLING' if self.variant != 'chaser' else 'CHASING'
                self.ai_state_timer_frames = 0
                self.patrol_range_x = (max(20, self.rect.x - random.randint(40,80)), min(SCREEN_WIDTH - self.rect.width - 20, self.rect.x + random.randint(40,80)))
        elif self.ai_state == 'PATROLLING':
            self.rect.y += self.current_speed_y
            self.current_speed_x = (self.current_speed_y * 0.5 + self.player_level_modifier * 0.1) * self.patrol_direction
            if self.rect.x <= self.patrol_range_x[0] or self.rect.x >= self.patrol_range_x[1]:
                self.patrol_direction *= -1
                self.current_speed_x = (self.current_speed_y * 0.5 + self.player_level_modifier * 0.1) * self.patrol_direction
            if self.variant == 'shooter' and self.rect.centery < SCREEN_HEIGHT * 0.55:
                self.shoot_action_timer_frames -= 1
                if self.shoot_action_timer_frames <= 0:
                    self.ai_state = 'AIMING_SHOT'
                    self.ai_state_timer_frames = 0
            if self.variant == 'dodger' and self.dodge_timer_frames <= 0:
                for p_bullet in player_bullet_list_ref:
                    detection_rect = self.rect.inflate(self.rect.width * 1.5, self.rect.height * 2)
                    if detection_rect.colliderect(p_bullet) and p_bullet.centery > self.rect.centery - 50:
                        self.ai_state = 'DODGING'
                        self.ai_state_timer_frames = 0
                        self.dodge_timer_frames = self.dodge_cooldown_frames + self.dodge_duration_frames
                        self.dodge_direction = 1 if p_bullet.centerx < self.rect.centerx else -1
                        break
            # New: For normal enemy, add a small chance to target and shoot the player
            if self.variant not in ['dodger', 'chaser', 'shooter']:
                if random.random() < 0.005:
                    self.ai_state = 'AIMING_SHOT'
                    self.ai_state_timer_frames = 0
        elif self.ai_state == 'CHASING':
            self.rect.y += self.current_speed_y * 0.9
            target_x_diff = player_main_rect.centerx - self.rect.centerx
            if abs(target_x_diff) > 5:
                self.current_speed_x = math.copysign(min(abs(target_x_diff * 0.05), self.current_speed_y * self.chase_aggressiveness), target_x_diff)
            if self.rect.centery < SCREEN_HEIGHT * 0.65:
                self.shoot_action_timer_frames -=1
                if self.shoot_action_timer_frames <= 0:
                    self.ai_state = 'AIMING_SHOT'
                    self.ai_state_timer_frames = 0
        elif self.ai_state == 'AIMING_SHOT':
            self.rect.y += self.current_speed_y * 0.3
            if self.ai_state_timer_frames > 20:
                dx_aim = player_main_rect.centerx - self.rect.centerx
                dy_aim = player_main_rect.bottom - self.rect.bottom
                dist_aim = math.hypot(dx_aim, dy_aim) if math.hypot(dx_aim, dy_aim) > 0 else 1
                # Increased multipliers for stronger shooting
                bullet_vel_x = (dx_aim / dist_aim) * (enemy_bullet_base_speed * 2.0 + self.player_level_modifier * 0.5)
                bullet_vel_y = (dy_aim / dist_aim) * (enemy_bullet_base_speed * 2.0 + self.player_level_modifier * 0.5)
                if bullet_vel_y <= 0:
                    bullet_vel_y = enemy_bullet_base_speed * 2.0
                enemy_bullets_master_list.append(EnemyProjectile(self.rect.centerx - 3, self.rect.bottom, bullet_vel_x, bullet_vel_y))
                self.shoot_action_timer_frames = self.shoot_action_cooldown_frames + random.randint(-10,10)
                # After shooting, immediately switch to DODGING to leave gap
                self.ai_state = 'DODGING'
                self.ai_state_timer_frames = 0
        elif self.ai_state == 'DODGING':
            self.rect.y += self.current_speed_y * 0.8
            self.current_speed_x = (self.current_speed_y * 2.5 + self.player_level_modifier * 0.3) * self.dodge_direction
            if self.ai_state_timer_frames > self.dodge_duration_frames:
                self.ai_state = 'PATROLLING'
                self.ai_state_timer_frames = 0
        if self.dodge_timer_frames > 0 and self.variant in ['dodger', 'chaser', 'shooter']:
            self.dodge_timer_frames -= 1

        self.rect.x += self.current_speed_x
        self.rect.clamp_ip(screen.get_rect())

        if self.rect.top > SCREEN_HEIGHT + 20: 
            return False
        return True

    def apply_damage(self, damage_amount):
        self.health_points -= damage_amount
        return self.health_points <= 0

    def draw_self(self, surface_to_draw_on):
        pygame.draw.rect(surface_to_draw_on, self.color_fill, self.rect)
        if show_debug_info:
            state_txt = small_hud_font.render(f"{self.variant[:3]}:{self.ai_state[:3]} H:{self.health_points}", True, DEBUG_TEXT_COLOR)
            surface_to_draw_on.blit(state_txt, (self.rect.x, self.rect.y - 18))

class EnemyProjectile:
    def __init__(self, x_pos, y_pos, vel_x, vel_y):
        self.rect = pygame.Rect(x_pos, y_pos, 7, 14)
        self.velocity_x = vel_x
        self.velocity_y = vel_y
        self.color_fill = ENEMY_BULLET_COLOR

    def update_pos(self):
        self.rect.x += self.velocity_x
        self.rect.y += self.velocity_y
        if not screen.get_rect().colliderect(self.rect): return False
        return True

    def draw_self(self, surface_to_draw_on):
        pygame.draw.rect(surface_to_draw_on, self.color_fill, self.rect)

def helper_draw_player_ship(surface_to_draw_on, player_current_rect, is_invincible_now, shield_is_active):
    ship_nose = (player_current_rect.centerx, player_current_rect.top)
    ship_left_wing = (player_current_rect.left, player_current_rect.bottom)
    ship_right_wing = (player_current_rect.right, player_current_rect.bottom)
    if is_invincible_now and (pygame.time.get_ticks() // 120) % 2 == 0: return
    pygame.draw.polygon(surface_to_draw_on, PLAYER_SHIP_COLOR, [ship_nose, ship_left_wing, ship_right_wing])
    cockpit_area_rect = pygame.Rect(player_current_rect.centerx - 6, player_current_rect.top + 12, 12, 12)
    pygame.draw.ellipse(surface_to_draw_on, WHITE, cockpit_area_rect)
    if shield_is_active:
        shield_alpha = 100 + (math.sin(pygame.time.get_ticks() * 0.01) * 50)
        shield_surf = pygame.Surface((player_current_rect.width + 20, player_current_rect.height + 20), pygame.SRCALPHA)
        pygame.draw.ellipse(shield_surf, (*POWER_UP_SHIELD_COLOR, int(shield_alpha)), shield_surf.get_rect(), 4)
        surface_to_draw_on.blit(shield_surf, (player_current_rect.left - 10, player_current_rect.top - 10))

def helper_draw_projectiles(surface_to_draw_on, projectile_list, projectile_color):
    for proj_rect in projectile_list:
        pygame.draw.rect(surface_to_draw_on, projectile_color, proj_rect)

def helper_draw_power_ups(surface_to_draw_on, p_ups_list):
    for pu_rect_item, pu_type_item in p_ups_list:
        color_to_use = POWER_UP_SHIELD_COLOR if pu_type_item == POWER_UP_TYPE_SHIELD else POWER_UP_MULTI_SHOT_COLOR
        pygame.draw.circle(surface_to_draw_on, color_to_use, pu_rect_item.center, pu_rect_item.width // 2)
        label = "S" if pu_type_item == POWER_UP_TYPE_SHIELD else "M"
        helper_draw_text_on_screen(surface_to_draw_on, label, hud_font, pu_rect_item.centerx, pu_rect_item.centery -15 , BLACK, center_txt=True)

def helper_draw_text_on_screen(surface_to_draw_on, text_to_show, font_obj, x_coord, y_coord, color_rgb, center_txt=True):
    text_surf_obj = font_obj.render(text_to_show, True, color_rgb)
    text_rect_obj = text_surf_obj.get_rect()
    if center_txt: text_rect_obj.midtop = (x_coord, y_coord)
    else: text_rect_obj.topleft = (x_coord, y_coord)
    surface_to_draw_on.blit(text_surf_obj, text_rect_obj)

def helper_calc_norm_dist(landmark_pt1, landmark_pt2):
    if ENABLE_CPP_ACCELERATION:
        return game_accelerator.calculate_landmark_distance(
            landmark_pt1.x, landmark_pt1.y, landmark_pt1.z,
            landmark_pt2.x, landmark_pt2.y, landmark_pt2.z)
    else:
        return math.sqrt((landmark_pt1.x - landmark_pt2.x)**2 + 
                        (landmark_pt1.y - landmark_pt2.y)**2 + 
                        (landmark_pt1.z - landmark_pt2.z)**2)

def helper_map_value(input_val, in_range_min, in_range_max, out_range_min, out_range_max):
    if (in_range_max - in_range_min) == 0: 
        return out_range_min
    
    if ENABLE_CPP_ACCELERATION:
        result = game_accelerator.map_finger_position(
            input_val, input_val,  # Using C++ function for accurate calculations
            in_range_min, in_range_max, 
            in_range_min, in_range_max,
            out_range_min, out_range_max,
            out_range_min, out_range_max)
        return result[0]
    else:
        return (input_val - in_range_min) * (out_range_max - out_range_min) / \
               (in_range_max - in_range_min) + out_range_min

def helper_draw_star_bg(surface_to_draw_on):
    for star_item in stars_list:
        star_item[1] += star_item[2]
        if star_item[1] > SCREEN_HEIGHT:
            star_item[1] = 0; star_item[0] = random.randint(0, SCREEN_WIDTH)
        pygame.draw.circle(surface_to_draw_on, STAR_COLOR, (int(star_item[0]), int(star_item[1])), star_item[2])

def helper_draw_boss(surface_to_draw_on, boss_main_r, boss_hp_curr, boss_hp_max):
    pygame.draw.rect(surface_to_draw_on, BOSS_COLOR, boss_main_r)
    pygame.draw.rect(surface_to_draw_on, DEEP_RED, boss_main_r.inflate(-20, -50)) 
    pygame.draw.circle(surface_to_draw_on, RED, (boss_main_r.centerx, boss_main_r.top + 30), 15)
    hp_bar_w = 150; hp_bar_h = 15
    hp_bar_x_pos = boss_main_r.centerx - hp_bar_w // 2
    hp_bar_y_pos = boss_main_r.top - hp_bar_h - 10
    curr_hp_w = int((boss_hp_curr / boss_hp_max) * hp_bar_w)
    if curr_hp_w < 0: curr_hp_w = 0
    pygame.draw.rect(surface_to_draw_on, BOSS_HEALTH_BAR_BG_COLOR, (hp_bar_x_pos, hp_bar_y_pos, hp_bar_w, hp_bar_h))
    pygame.draw.rect(surface_to_draw_on, BOSS_HEALTH_BAR_COLOR, (hp_bar_x_pos, hp_bar_y_pos, curr_hp_w, hp_bar_h))

def webcam_calibration_test():
    """Test camera and hand detection before starting the game"""
    calibration_running = True
    hand_detected_count = 0
    required_hand_detections = 15  # Number of frames hand must be detected
    finger_detection_confirmed = False
    fingers_detected_frames = 0
    
    calibration_start_time = pygame.time.get_ticks()
    calibration_timeout_ms = 30000  # 30 second timeout
    
    while calibration_running:
        current_time_calib_ms = pygame.time.get_ticks()
        
        # Check timeout
        if current_time_calib_ms - calibration_start_time > calibration_timeout_ms:
            screen.fill(BLACK)
            helper_draw_star_bg(screen)
            helper_draw_text_on_screen(screen, "CALIBRATION TIMEOUT!", title_font, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60, RED)
            helper_draw_text_on_screen(screen, "Please ensure your camera is working", main_font, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20, WHITE)
            helper_draw_text_on_screen(screen, "and your hand is visible.", main_font, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80, WHITE)
            pygame.display.flip()
            pygame.time.wait(3000)
            return False
        
        # Read frame from camera
        ret_calib, frame_calib = webcam_capture.read()
        if not ret_calib:
            continue
        
        frame_calib_flipped = cv2.flip(frame_calib, 1)
        frame_calib_rgb = cv2.cvtColor(frame_calib_flipped, cv2.COLOR_BGR2RGB)
        hand_results_calib = hands_detector.process(frame_calib_rgb)
        
        # Display frame with hand drawn
        display_frame = frame_calib_flipped.copy()
        status_text = "Calibration: Show your hand..."
        status_color = (0, 165, 255)  # Orange
        
        if hand_results_calib.multi_hand_landmarks:
            hand_detected_count += 1
            fingers_detected_frames += 1
            status_text = f"Hand Detected! Keep it steady... ({hand_detected_count}/{required_hand_detections})"
            status_color = (0, 255, 0)  # Green
            
            # Draw hand
            mp_drawing.draw_landmarks(display_frame, hand_results_calib.multi_hand_landmarks[0], mp_hands.HAND_CONNECTIONS,
                                      mp_drawing_styles.get_default_hand_landmarks_style(), 
                                      mp_drawing_styles.get_default_hand_connections_style())
            
            # Check if all fingers are detected
            if len(hand_results_calib.multi_hand_landmarks[0].landmark) >= 21:
                finger_detection_confirmed = True
            
            # If hand was detected long enough
            if hand_detected_count >= required_hand_detections and finger_detection_confirmed:
                calibration_running = False
        else:
            hand_detected_count = max(0, hand_detected_count - 2)  # Gradually decrease if hand is out of range
            fingers_detected_frames = 0
        
        # Display status text
        cv2.putText(display_frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        cv2.putText(display_frame, "Press 'q' to quit", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Display progress bar
        progress_bar_width = 300
        progress_bar_height = 30
        progress_bar_x = display_frame.shape[1] // 2 - progress_bar_width // 2
        progress_bar_y = display_frame.shape[0] - 100
        progress = min(100, (hand_detected_count / required_hand_detections) * 100)
        filled_width = int(progress_bar_width * (progress / 100))
        
        cv2.rectangle(display_frame, (progress_bar_x, progress_bar_y), 
                      (progress_bar_x + progress_bar_width, progress_bar_y + progress_bar_height), 
                      (255, 255, 255), 2)
        cv2.rectangle(display_frame, (progress_bar_x, progress_bar_y), 
                      (progress_bar_x + filled_width, progress_bar_y + progress_bar_height), 
                      (0, 255, 0), -1)
        
        cv2.imshow('Webcam Calibration Test', display_frame)
        
        # Check for exit
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            cv2.destroyWindow('Webcam Calibration Test')
            return False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
    
    # Display success message
    cv2.destroyWindow('Webcam Calibration Test')
    screen.fill(BLACK)
    helper_draw_star_bg(screen)
    helper_draw_text_on_screen(screen, "CALIBRATION SUCCESSFUL!", title_font, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60, GREEN)
    helper_draw_text_on_screen(screen, "Your camera and hand detection are ready!", main_font, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20, WHITE)
    helper_draw_text_on_screen(screen, "Starting game in 2 seconds...", main_font, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80, YELLOW)
    pygame.display.flip()
    pygame.time.wait(2000)
    
    return True

def game_logic_reset_all_params():
    global player_rect, player_lives, score, all_enemies_list, player_bullets_list, enemy_bullets_master_list, boss_bullets_master_list, power_ups_list
    global current_game_state, current_level, score_for_next_level, boss_active, boss_current_health, boss_main_rect, boss_state, boss_current_phase
    global enemy_spawn_timer, player_invincible_until_ms, active_explosions_list
    global player_shield_active, player_shield_end_time_ms, player_multi_shot_active, player_multi_shot_end_time_ms
    global player_current_shoot_cooldown_ms, enemy_spawn_rate_current

    player_rect.centerx = SCREEN_WIDTH // 2
    player_rect.centery = SCREEN_HEIGHT * 0.75
    player_lives = player_lives_start
    score = 0
    all_enemies_list = []
    player_bullets_list = []
    enemy_bullets_master_list = []
    boss_bullets_master_list = []
    power_ups_list = []
    active_explosions_list = []
    current_level = 1
    score_for_next_level = score_to_next_level_base * current_level
    boss_active = False
    boss_current_health = boss_max_health_base * current_level
    boss_main_rect.centerx = SCREEN_WIDTH // 2
    boss_main_rect.top = 40
    boss_state = "ENTERING"
    boss_current_phase = 1
    enemy_spawn_timer = 0
    enemy_spawn_rate_current = enemy_spawn_rate_initial
    player_invincible_until_ms = 0
    player_shield_active = False
    player_shield_end_time_ms = 0
    player_multi_shot_active = False
    player_multi_shot_end_time_ms = 0
    player_current_shoot_cooldown_ms = player_base_shoot_cooldown_ms
    current_game_state = GAME_STATE_INSTRUCTIONS

enemy_spawn_timer = 0
is_game_running = True
is_webcam_window_active = False
was_hand_detected_this_frame = False
game_logic_reset_all_params()

while is_game_running:
    current_time_ms_loop = pygame.time.get_ticks()
    loop_delta_time_s = clock.tick(90) / 1000.0

    for event_item in pygame.event.get():
        if event_item.type == pygame.QUIT: is_game_running = False
        if event_item.type == pygame.KEYDOWN:
            if event_item.key == pygame.K_d: show_debug_info = not show_debug_info
            if current_game_state == GAME_STATE_GAME_OVER and event_item.key == pygame.K_r:
                game_logic_reset_all_params()
            if current_game_state == GAME_STATE_INSTRUCTIONS and event_item.key == pygame.K_SPACE:
                 # تست دوربین و شناسایی دست
                 if webcam_calibration_test():
                     current_game_state = GAME_STATE_PLAYING
                     player_invincible_until_ms = current_time_ms_loop + player_invincibility_duration_ms
                 else:
                     # اگر تست دوربین ناموفق بود، در صفحه تعلیمات بماند
                     pass

    finger_x_norm_val = None
    finger_y_norm_val = None
    are_fingers_pinched = False
    was_webcam_frame_read, webcam_rgb_frame = webcam_capture.read()
    if was_webcam_frame_read:
        webcam_rgb_frame_flipped = cv2.flip(webcam_rgb_frame, 1)
        cv2_rgb_frame_for_mediapipe = cv2.cvtColor(webcam_rgb_frame_flipped, cv2.COLOR_BGR2RGB)
        mediapipe_hand_results = hands_detector.process(cv2_rgb_frame_for_mediapipe)
        webcam_display_frame = webcam_rgb_frame_flipped.copy()

        if mediapipe_hand_results.multi_hand_landmarks:
            was_hand_detected_this_frame = True
            if current_game_state == GAME_STATE_PAUSED_NO_HAND: current_game_state = GAME_STATE_PLAYING
            current_hand_landmarks = mediapipe_hand_results.multi_hand_landmarks[0].landmark
            finger_x_norm_val = current_hand_landmarks[INDEX_FINGER_TIP_ID].x
            finger_y_norm_val = current_hand_landmarks[INDEX_FINGER_TIP_ID].y
            thumb_index_dist = helper_calc_norm_dist(current_hand_landmarks[THUMB_TIP_ID], current_hand_landmarks[INDEX_FINGER_TIP_ID])
            if thumb_index_dist < PINCH_GESTURE_THRESHOLD: are_fingers_pinched = True
            if is_webcam_window_active:
                mp_drawing.draw_landmarks(webcam_display_frame, mediapipe_hand_results.multi_hand_landmarks[0], mp_hands.HAND_CONNECTIONS,
                                          mp_drawing_styles.get_default_hand_landmarks_style(), mp_drawing_styles.get_default_hand_connections_style())
        else:
            was_hand_detected_this_frame = False
            if current_game_state in [GAME_STATE_PLAYING, GAME_STATE_BOSS_FIGHT]:
                current_game_state = GAME_STATE_PAUSED_NO_HAND

        if is_webcam_window_active:
            try:
                cv2.imshow('Webcam Feed (Q to close)', webcam_display_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    is_webcam_window_active = False; cv2.destroyWindow('Webcam Feed (Q to close)')
            except cv2.error: is_webcam_window_active = False
    
    is_player_blinking_invincible = current_time_ms_loop < player_invincible_until_ms
    
    if player_shield_active and current_time_ms_loop > player_shield_end_time_ms:
        player_shield_active = False
    if player_multi_shot_active and current_time_ms_loop > player_multi_shot_end_time_ms:
        player_multi_shot_active = False
        player_current_shoot_cooldown_ms = player_base_shoot_cooldown_ms

    if current_game_state == GAME_STATE_INSTRUCTIONS:
        screen.fill(BLACK); helper_draw_star_bg(screen)
        helper_draw_text_on_screen(screen, "COSMIC FINGER BLASTER", title_font, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4 - 70, ORANGE)
        helper_draw_text_on_screen(screen, "Index: Move Ship (All Dirs)", main_font, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100, WHITE)
        helper_draw_text_on_screen(screen, "Pinch: Shoot", main_font, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50, WHITE)
        helper_draw_text_on_screen(screen, "Survive the Alien Onslaught!", main_font, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 0, GREEN)
        helper_draw_text_on_screen(screen, "Press SPACE to Engage", main_font, SCREEN_WIDTH // 2, SCREEN_HEIGHT * 3 // 4 + 0, WHITE)
        helper_draw_text_on_screen(screen, "D for Debug", small_hud_font, SCREEN_WIDTH // 2, SCREEN_HEIGHT * 3 // 4 + 60, YELLOW)
        pygame.display.flip(); continue
    elif current_game_state == GAME_STATE_GAME_OVER:
        screen.fill(BLACK); helper_draw_star_bg(screen)
        helper_draw_text_on_screen(screen, "MISSION FAILED!", title_font, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3, RED)
        helper_draw_text_on_screen(screen, f"SCORE: {score}", main_font, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20, WHITE)
        helper_draw_text_on_screen(screen, f"LEVEL: {current_level}", main_font, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30, WHITE)
        helper_draw_text_on_screen(screen, "Press 'R' to Retry", main_font, SCREEN_WIDTH // 2, SCREEN_HEIGHT * 2 // 3 + 20, YELLOW)
        pygame.display.flip(); continue
    elif current_game_state == GAME_STATE_PAUSED_NO_HAND:
        screen.fill(BLACK); helper_draw_star_bg(screen)
        helper_draw_text_on_screen(screen, "AWAITING COMMAND INPUT!", title_font, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60, ORANGE)
        helper_draw_text_on_screen(screen, "Show Hand to Resume Combat", main_font, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10, WHITE)
        helper_draw_text_on_screen(screen, f"Score: {score}", hud_font, 20, 20, WHITE, False)
        helper_draw_text_on_screen(screen, f"Level: {current_level}", hud_font, 20, 55, WHITE, False)
        helper_draw_text_on_screen(screen, "Lives: " + "♥ " * player_lives, hud_font, SCREEN_WIDTH - 180, 20, WHITE, False)
        pygame.display.flip(); continue
    elif current_game_state == GAME_STATE_LEVEL_UP:
        screen.fill(BLACK); helper_draw_star_bg(screen)
        helper_draw_text_on_screen(screen, f"LEVEL {current_level} ENGAGED!", title_font, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40, GREEN)
        if current_time_ms_loop > level_up_message_end_time_ms:
            if current_level >= boss_fight_trigger_level and not boss_active:
                current_game_state = GAME_STATE_BOSS_FIGHT; boss_active = True
                boss_current_health = boss_max_health_base * (1 + (current_level - boss_fight_trigger_level) * 0.5)
                boss_current_health = int(boss_current_health)
                all_enemies_list = [] 
                boss_state = "ENTERING"; boss_current_phase = 1
            else: current_game_state = GAME_STATE_PLAYING
        pygame.display.flip(); continue

    if finger_x_norm_val is not None:
        player_rect.centerx = int(helper_map_value(finger_x_norm_val, 0.12, 0.88, 0, SCREEN_WIDTH))
    if finger_y_norm_val is not None:
        player_rect.centery = int(helper_map_value(finger_y_norm_val, 0.2, 0.8, PLAYER_PLAYABLE_Y_MIN, PLAYER_PLAYABLE_Y_MAX))

    player_rect.left = max(0, player_rect.left); player_rect.right = min(SCREEN_WIDTH, player_rect.right)
    player_rect.top = max(PLAYER_PLAYABLE_Y_MIN, player_rect.top); player_rect.bottom = min(PLAYER_PLAYABLE_Y_MAX + player_height // 2, player_rect.bottom)


    if are_fingers_pinched and current_time_ms_loop - player_last_shot_time_ms > player_current_shoot_cooldown_ms:
        base_bullet_rect = pygame.Rect(player_rect.centerx - player_bullet_width // 2, player_rect.top, player_bullet_width, player_bullet_height)
        player_bullets_list.append(base_bullet_rect)
        if player_multi_shot_active:
            player_bullets_list.append(pygame.Rect(player_rect.left, player_rect.centery - player_bullet_height // 2, player_bullet_width, player_bullet_height))
            player_bullets_list.append(pygame.Rect(player_rect.right - player_bullet_width, player_rect.centery - player_bullet_height // 2, player_bullet_width, player_bullet_height))
        player_last_shot_time_ms = current_time_ms_loop

    player_bullets_list[:] = [b_rect for b_rect in player_bullets_list if b_rect.bottom > 0]; [b_rect.move_ip(0, -player_bullet_speed) for b_rect in player_bullets_list]
    enemy_bullets_master_list[:] = [eb_obj for eb_obj in enemy_bullets_master_list if eb_obj.update_pos()]

    if current_game_state == GAME_STATE_PLAYING:
        enemy_spawn_timer += 1
        enemy_spawn_rate_current = max(15, enemy_spawn_rate_initial - (current_level -1) * 4)
        if enemy_spawn_timer >= enemy_spawn_rate_current:
            enemy_spawn_timer = 0
            spawn_x_pos = random.randint(0, SCREEN_WIDTH - enemy_width_std)
            enemy_variant_roll = random.random() + (current_level -1) * 0.03
            if enemy_variant_roll < 0.35: new_enemy = EnemyAI(spawn_x_pos, -enemy_height_std, 'normal', current_level)
            elif enemy_variant_roll < 0.60: new_enemy = EnemyAI(spawn_x_pos, -enemy_height_std, 'shooter', current_level)
            elif enemy_variant_roll < 0.80: new_enemy = EnemyAI(spawn_x_pos, -enemy_height_std, 'chaser', current_level)
            else: new_enemy = EnemyAI(spawn_x_pos, -enemy_height_std, 'dodger', current_level)
            all_enemies_list.append(new_enemy)
    
    enemies_to_keep_list = []
    for enemy_instance in all_enemies_list:
        if enemy_instance.update_behavior(player_rect, player_bullets_list, all_enemies_list):
            enemies_to_keep_list.append(enemy_instance)
    all_enemies_list = enemies_to_keep_list

    if boss_active and current_game_state == GAME_STATE_BOSS_FIGHT:
        boss_state_timer += 1
        if boss_state == "ENTERING":
            boss_main_rect.y += base_enemy_speed_y * 0.5
            if boss_main_rect.top >= 40:
                boss_state = "PHASE_1_ATTACK"
                boss_state_timer = 0
        elif boss_state == "PHASE_1_ATTACK":
            boss_main_rect.x += boss_speed_x_current
            if boss_main_rect.left < 0 or boss_main_rect.right > SCREEN_WIDTH: boss_speed_x_current *= -1
            if current_time_ms_loop - boss_last_shot_time_ms > boss_base_shoot_cooldown_ms:
                num_shots = 3 + boss_current_phase
                angle_spread = math.pi / (num_shots +1) 
                for i in range(num_shots):
                    angle = (i+1) * angle_spread - (math.pi/2) + random.uniform(-0.1,0.1)
                    b_vel_x = math.cos(angle) * (enemy_bullet_base_speed + 1.5 + boss_current_phase)
                    b_vel_y = math.sin(angle) * (enemy_bullet_base_speed + 1.5 + boss_current_phase)
                    if b_vel_y <= 0 : b_vel_y = (enemy_bullet_base_speed + 1.5 + boss_current_phase)
                    boss_bullets_master_list.append(EnemyProjectile(boss_main_rect.centerx -3 + (i - num_shots//2)*20 , boss_main_rect.bottom, b_vel_x, b_vel_y))
                boss_last_shot_time_ms = current_time_ms_loop
            
            if boss_current_health < boss_max_health_base * boss_phase_change_health_threshold_factor * (1 + (current_level - boss_fight_trigger_level) * 0.5) and boss_current_phase == 1:
                boss_current_phase = 2
                boss_state = "PHASE_TRANSITION"
                boss_state_timer = 0
                active_explosions_list.append(Explosion(boss_main_rect.center, 30, 60, 600, colors=[BOSS_SPECIAL_ATTACK_COLOR]))
        elif boss_state == "PHASE_TRANSITION":
            boss_main_rect.x += random.randint(-5,5)
            boss_main_rect.y += random.randint(-2,2)
            boss_main_rect.clamp_ip(screen.get_rect())
            if boss_state_timer > 120 :
                boss_state = "PHASE_2_ATTACK"
                boss_state_timer = 0
                boss_base_shoot_cooldown_ms = max(300, boss_base_shoot_cooldown_ms - 150)
                boss_speed_x_current *= 1.3
        elif boss_state == "PHASE_2_ATTACK":
            boss_main_rect.x += boss_speed_x_current
            if boss_main_rect.left < 0 or boss_main_rect.right > SCREEN_WIDTH: boss_speed_x_current *= -1
            if current_time_ms_loop - boss_last_shot_time_ms > boss_base_shoot_cooldown_ms:
                for i in range(-2,3):
                    dx_aim_boss = player_rect.centerx - (boss_main_rect.centerx + i * 30) 
                    dy_aim_boss = SCREEN_HEIGHT
                    dist_aim_boss = math.hypot(dx_aim_boss, dy_aim_boss) if math.hypot(dx_aim_boss, dy_aim_boss) > 0 else 1
                    b_vel_x_boss = (dx_aim_boss / dist_aim_boss) * (enemy_bullet_base_speed + 3 + boss_current_phase)
                    b_vel_y_boss = (dy_aim_boss / dist_aim_boss) * (enemy_bullet_base_speed + 3 + boss_current_phase)
                    if b_vel_y_boss <= 0: b_vel_y_boss = (enemy_bullet_base_speed + 3 + boss_current_phase)
                    boss_bullets_master_list.append(EnemyProjectile(boss_main_rect.centerx -3 + i * 30, boss_main_rect.bottom, b_vel_x_boss, b_vel_y_boss))
                boss_last_shot_time_ms = current_time_ms_loop

        boss_bullets_master_list[:] = [bb_obj for bb_obj in boss_bullets_master_list if bb_obj.update_pos()]
        player_bullets_hit_boss_indices = []
        for idx, p_b in enumerate(player_bullets_list):
            if p_b.colliderect(boss_main_rect):
                player_bullets_hit_boss_indices.append(idx)
                boss_current_health -= 1
                score += 20
                active_explosions_list.append(Explosion(p_b.center, 7, 18, 250))
                if boss_current_health <= 0:
                    score += 750 * current_level; active_explosions_list.append(Explosion(boss_main_rect.center, 100, 150, 2000))
                    boss_active = False; current_game_state = GAME_STATE_PLAYING 
                    pu_rect = pygame.Rect(boss_main_rect.centerx - 20, boss_main_rect.centery - 20, 40, 40)
                    power_ups_list.append([pu_rect, random.choice([POWER_UP_TYPE_SHIELD, POWER_UP_TYPE_MULTI_SHOT])])
                    break
        player_bullets_list = [b for i, b in enumerate(player_bullets_list) if i not in player_bullets_hit_boss_indices]

        if not is_player_blinking_invincible and not player_shield_active:
            for b_b_obj in boss_bullets_master_list:
                if player_rect.colliderect(b_b_obj.rect):
                    boss_bullets_master_list.remove(b_b_obj)
                    player_lives -=1; active_explosions_list.append(Explosion(player_rect.center))
                    if player_lives > 0: player_invincible_until_ms = current_time_ms_loop + player_invincibility_duration_ms
                    else: current_game_state = GAME_STATE_GAME_OVER
                    break
    
    power_ups_list[:] = [pu_item for pu_item in power_ups_list if pu_item[0].top < SCREEN_HEIGHT]; [pu_item[0].move_ip(0, base_enemy_speed_y * 0.6) for pu_item in power_ups_list]

    player_b_to_remove_indices = set()
    enemies_hit_this_frame_indices = set()
    
    if ENABLE_CPP_ACCELERATION and len(player_bullets_list) > 0 and len(all_enemies_list) > 0:
        # تبدیل به فرمت سازگار با C++
        bullets_data = [[b.x, b.y] for b in player_bullets_list]
        enemies_data = [[e.rect.x, e.rect.y] for e in all_enemies_list]
        
        collisions = game_accelerator.check_bullet_enemy_collisions(
            bullets_data, enemies_data,
            player_bullet_width, player_bullet_height,
            enemy_width_std, enemy_height_std)
        
        for pb_idx, en_idx in collisions:
            player_b_to_remove_indices.add(pb_idx)
            active_explosions_list.append(Explosion(all_enemies_list[en_idx].rect.center, 12, 30, 350))
            if all_enemies_list[en_idx].apply_damage(1):
                enemies_hit_this_frame_indices.add(en_idx)
                score += 15 * all_enemies_list[en_idx].player_level_modifier
                if random.random() < power_up_base_drop_chance + (current_level -1)*0.01:
                    pu_rect = pygame.Rect(all_enemies_list[en_idx].rect.centerx - 18, all_enemies_list[en_idx].rect.centery - 18, 36, 36)
                    power_ups_list.append([pu_rect, random.choice([POWER_UP_TYPE_SHIELD, POWER_UP_TYPE_MULTI_SHOT])])
    else:
        # استفاده از روش Python معمول
        for pb_idx, p_bullet_rect in enumerate(player_bullets_list):
            for en_idx, enemy_obj_item in enumerate(all_enemies_list):
                if en_idx in enemies_hit_this_frame_indices: continue
                if p_bullet_rect.colliderect(enemy_obj_item.rect):
                    player_b_to_remove_indices.add(pb_idx)
                    active_explosions_list.append(Explosion(enemy_obj_item.rect.center, 12, 30, 350))
                    if enemy_obj_item.apply_damage(1):
                        enemies_hit_this_frame_indices.add(en_idx)
                        score += 15 * enemy_obj_item.player_level_modifier
                        if random.random() < power_up_base_drop_chance + (current_level -1)*0.01:
                            pu_rect = pygame.Rect(enemy_obj_item.rect.centerx - 18, enemy_obj_item.rect.centery - 18, 36, 36)
                            power_ups_list.append([pu_rect, random.choice([POWER_UP_TYPE_SHIELD, POWER_UP_TYPE_MULTI_SHOT])])
                    break
    
    player_bullets_list = [pb for i, pb in enumerate(player_bullets_list) if i not in player_b_to_remove_indices]
    all_enemies_list = [en for i, en in enumerate(all_enemies_list) if i not in enemies_hit_this_frame_indices]

    if not is_player_blinking_invincible and not player_shield_active:
        if ENABLE_CPP_ACCELERATION and len(all_enemies_list) > 0:
            enemies_data = [[e.rect.x, e.rect.y] for e in all_enemies_list]
            collisions = game_accelerator.check_player_enemy_collisions(
                [player_rect.x, player_rect.y], enemies_data,
                player_width, player_height,
                enemy_width_std, enemy_height_std)
            
            if collisions:
                idx_en = collisions[0]
                enemy_obj_item_coll = all_enemies_list[idx_en]
                all_enemies_list.pop(idx_en)
                player_lives -= 1
                active_explosions_list.append(Explosion(player_rect.center, num_particles=30, max_radius=50))
                active_explosions_list.append(Explosion(enemy_obj_item_coll.rect.center))
                if player_lives > 0: player_invincible_until_ms = current_time_ms_loop + player_invincibility_duration_ms
                else: current_game_state = GAME_STATE_GAME_OVER
        else:
            for idx_en, enemy_obj_item_coll in enumerate(all_enemies_list):
                if player_rect.colliderect(enemy_obj_item_coll.rect):
                    all_enemies_list.pop(idx_en)
                    player_lives -= 1
                    active_explosions_list.append(Explosion(player_rect.center, num_particles=30, max_radius=50))
                    active_explosions_list.append(Explosion(enemy_obj_item_coll.rect.center))
                    if player_lives > 0: player_invincible_until_ms = current_time_ms_loop + player_invincibility_duration_ms
                    else: current_game_state = GAME_STATE_GAME_OVER
                    break
    
    if not is_player_blinking_invincible and not player_shield_active:
        for idx_eb, eb_projectile_obj in enumerate(enemy_bullets_master_list):
            if player_rect.colliderect(eb_projectile_obj.rect):
                enemy_bullets_master_list.pop(idx_eb)
                player_lives -= 1
                active_explosions_list.append(Explosion(player_rect.center))
                if player_lives > 0: player_invincible_until_ms = current_time_ms_loop + player_invincibility_duration_ms
                else: current_game_state = GAME_STATE_GAME_OVER
                break
                
    for idx_pu, pu_item_data in enumerate(power_ups_list):
        pu_item_rect, pu_item_type = pu_item_data
        
        if ENABLE_CPP_ACCELERATION:
            collision = game_accelerator.player_bullet_collision(
                player_rect.x, player_rect.y, player_width, player_height,
                pu_item_rect.x, pu_item_rect.y, pu_item_rect.width, pu_item_rect.height)
            
            if collision:
                power_ups_list.pop(idx_pu)
                if pu_item_type == POWER_UP_TYPE_SHIELD:
                    player_shield_active = True
                    player_shield_end_time_ms = current_time_ms_loop + player_shield_duration_ms
                elif pu_item_type == POWER_UP_TYPE_MULTI_SHOT:
                    player_multi_shot_active = True
                    player_multi_shot_end_time_ms = current_time_ms_loop + player_multi_shot_duration_ms
                    player_current_shoot_cooldown_ms = player_base_shoot_cooldown_ms // 2
                break
        else:
            if player_rect.colliderect(pu_item_rect):
                power_ups_list.pop(idx_pu)
                if pu_item_type == POWER_UP_TYPE_SHIELD:
                    player_shield_active = True
                    player_shield_end_time_ms = current_time_ms_loop + player_shield_duration_ms
                elif pu_item_type == POWER_UP_TYPE_MULTI_SHOT:
                    player_multi_shot_active = True
                    player_multi_shot_end_time_ms = current_time_ms_loop + player_multi_shot_duration_ms
                    player_current_shoot_cooldown_ms = player_base_shoot_cooldown_ms // 2
                break

    if score >= score_for_next_level and current_game_state == GAME_STATE_PLAYING:
        current_level += 1
        score_for_next_level += score_to_next_level_base * (1 + current_level * 0.2)
        current_game_state = GAME_STATE_LEVEL_UP
        level_up_message_end_time_ms = current_time_ms_loop + level_up_message_duration_ms
        player_invincible_until_ms = current_time_ms_loop + player_invincibility_duration_ms + 1000

    active_explosions_list = [expl_obj for expl_obj in active_explosions_list if expl_obj.update()]

    screen.fill(BLACK); helper_draw_star_bg(screen)
    for enemy_instance_draw in all_enemies_list: enemy_instance_draw.draw_self(screen)
    for eb_proj_obj_draw in enemy_bullets_master_list: eb_proj_obj_draw.draw_self(screen)
    helper_draw_projectiles(screen, player_bullets_list, PLAYER_BULLET_COLOR)
    helper_draw_power_ups(screen, power_ups_list)
    if boss_active:
        effective_boss_max_health = boss_max_health_base * (1 + (current_level - boss_fight_trigger_level) * 0.5) if current_level >= boss_fight_trigger_level else boss_max_health_base
        helper_draw_boss(screen, boss_main_rect, boss_current_health, effective_boss_max_health)
        for bb_proj_obj_draw in boss_bullets_master_list: bb_proj_obj_draw.draw_self(screen)
    helper_draw_player_ship(screen, player_rect, is_player_blinking_invincible, player_shield_active)
    for expl_obj_draw in active_explosions_list: expl_obj_draw.draw(screen)

    helper_draw_text_on_screen(screen, f"Score: {score}", hud_font, 20, 15, WHITE, False)
    helper_draw_text_on_screen(screen, f"Level: {current_level}", hud_font, 20, 50, WHITE, False)
    helper_draw_text_on_screen(screen, "Lives: " + "♥ " * player_lives, hud_font, SCREEN_WIDTH - 200, 15, WHITE, False)
    if player_shield_active:
         helper_draw_text_on_screen(screen, "SHIELD ACTIVE!", hud_font, SCREEN_WIDTH // 2, 15, POWER_UP_SHIELD_COLOR, True)
    elif player_multi_shot_active:
         helper_draw_text_on_screen(screen, "MULTI-SHOT!", hud_font, SCREEN_WIDTH // 2, 15, POWER_UP_MULTI_SHOT_COLOR, True)
    
    if show_debug_info:
        debug_y = SCREEN_HEIGHT - 100
        helper_draw_text_on_screen(screen, f"FPS: {int(clock.get_fps())}", small_hud_font, 10, debug_y, DEBUG_TEXT_COLOR, False)
        helper_draw_text_on_screen(screen, f"Enemies: {len(all_enemies_list)}", small_hud_font, 10, debug_y + 20, DEBUG_TEXT_COLOR, False)
        helper_draw_text_on_screen(screen, f"P_Bull: {len(player_bullets_list)} E_Bull: {len(enemy_bullets_master_list)} B_Bull: {len(boss_bullets_master_list)}", small_hud_font, 10, debug_y+40, DEBUG_TEXT_COLOR, False)
        helper_draw_text_on_screen(screen, f"State: {current_game_state}", small_hud_font, 10, debug_y+60, DEBUG_TEXT_COLOR, False)


    pygame.display.flip()

webcam_capture.release()
if is_webcam_window_active:
    try: cv2.destroyAllWindows()
    except: pass
pygame.quit()
