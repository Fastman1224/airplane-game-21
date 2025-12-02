#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <cmath>
#include <vector>
#include <algorithm>

namespace py = pybind11;

// Struct for rectangle collision
struct Rect {
    float x, y, width, height;
    
    Rect(float x = 0, float y = 0, float w = 0, float h = 0) 
        : x(x), y(y), width(w), height(h) {}
    
    bool collides_with(const Rect& other) const {
        return !(x + width < other.x || other.x + other.width < x ||
                 y + height < other.y || other.y + other.height < y);
    }
    
    float distance_to(const Rect& other) const {
        float dx = (x + width/2) - (other.x + other.width/2);
        float dy = (y + height/2) - (other.y + other.height/2);
        return std::sqrt(dx*dx + dy*dy);
    }
};

// Struct for vector 3D
struct Vector3D {
    float x, y, z;
    
    Vector3D(float x = 0, float y = 0, float z = 0) : x(x), y(y), z(z) {}
    
    float distance_to(const Vector3D& other) const {
        float dx = x - other.x;
        float dy = y - other.y;
        float dz = z - other.z;
        return std::sqrt(dx*dx + dy*dy + dz*dz);
    }
};

// Fast collision detection function for bullets and enemies
std::vector<std::pair<int, int>> check_bullet_enemy_collisions(
    const std::vector<std::vector<float>>& bullets,
    const std::vector<std::vector<float>>& enemies,
    float bullet_w, float bullet_h,
    float enemy_w, float enemy_h) {
    
    std::vector<std::pair<int, int>> collisions;
    
    for (size_t b_idx = 0; b_idx < bullets.size(); ++b_idx) {
        Rect bullet(bullets[b_idx][0], bullets[b_idx][1], bullet_w, bullet_h);
        
        for (size_t e_idx = 0; e_idx < enemies.size(); ++e_idx) {
            Rect enemy(enemies[e_idx][0], enemies[e_idx][1], enemy_w, enemy_h);
            
            if (bullet.collides_with(enemy)) {
                collisions.push_back({b_idx, e_idx});
            }
        }
    }
    
    return collisions;
}

// Collision detection function for player and enemies
std::vector<int> check_player_enemy_collisions(
    const std::vector<float>& player,
    const std::vector<std::vector<float>>& enemies,
    float player_w, float player_h,
    float enemy_w, float enemy_h) {
    
    std::vector<int> collisions;
    Rect player_rect(player[0], player[1], player_w, player_h);
    
    for (size_t e_idx = 0; e_idx < enemies.size(); ++e_idx) {
        Rect enemy(enemies[e_idx][0], enemies[e_idx][1], enemy_w, enemy_h);
        
        if (player_rect.collides_with(enemy)) {
            collisions.push_back(e_idx);
        }
    }
    
    return collisions;
}

// Function to calculate distance for hand detection
float calculate_landmark_distance(
    float x1, float y1, float z1,
    float x2, float y2, float z2) {
    
    float dx = x1 - x2;
    float dy = y1 - y2;
    float dz = z1 - z2;
    return std::sqrt(dx*dx + dy*dy + dz*dz);
}

// Function to check pinch gesture
bool is_pinch_detected(
    float thumb_x, float thumb_y, float thumb_z,
    float index_x, float index_y, float index_z,
    float threshold) {
    
    float dist = calculate_landmark_distance(
        thumb_x, thumb_y, thumb_z,
        index_x, index_y, index_z
    );
    
    return dist < threshold;
}

// Function to calculate finger position mapping
std::vector<float> map_finger_position(
    float norm_x, float norm_y,
    float in_x_min, float in_x_max, float in_y_min, float in_y_max,
    float out_x_min, float out_x_max, float out_y_min, float out_y_max) {
    
    float screen_x = (norm_x - in_x_min) * (out_x_max - out_x_min) / 
                     (in_x_max - in_x_min) + out_x_min;
    float screen_y = (norm_y - in_y_min) * (out_y_max - out_y_min) / 
                     (in_y_max - in_y_min) + out_y_min;
    
    return {screen_x, screen_y};
}

// Update enemy positions
std::vector<std::vector<float>> update_enemy_positions(
    const std::vector<std::vector<float>>& enemies,
    const std::vector<float>& enemy_speeds,
    int screen_width, int screen_height) {
    
    auto result = enemies;
    
    for (size_t i = 0; i < result.size(); ++i) {
        result[i][0] += result[i][4]; // speed_x
        result[i][1] += enemy_speeds[i]; // speed_y
        
        // boundary checks
        if (result[i][0] < 0) result[i][0] = 0;
        if (result[i][0] > screen_width) result[i][0] = screen_width;
    }
    
    return result;
}

// Function to calculate enemy firing direction
std::vector<float> calculate_aim_direction(
    float enemy_x, float enemy_y,
    float player_x, float player_y) {
    
    float dx = player_x - enemy_x;
    float dy = player_y - enemy_y;
    float dist = std::sqrt(dx*dx + dy*dy);
    
    if (dist == 0) return {0, 0};
    
    return {dx / dist, dy / dist};
}

// Function to check bullet-boss collision
bool bullet_boss_collision(
    float bullet_x, float bullet_y, float bullet_w, float bullet_h,
    float boss_x, float boss_y, float boss_w, float boss_h) {
    
    Rect bullet(bullet_x, bullet_y, bullet_w, bullet_h);
    Rect boss(boss_x, boss_y, boss_w, boss_h);
    
    return bullet.collides_with(boss);
}

// Function to check player-bullet collision
bool player_bullet_collision(
    float player_x, float player_y, float player_w, float player_h,
    float bullet_x, float bullet_y, float bullet_w, float bullet_h) {
    
    Rect player(player_x, player_y, player_w, player_h);
    Rect bullet(bullet_x, bullet_y, bullet_w, bullet_h);
    
    return player.collides_with(bullet);
}

// Function to calculate distance between points
float point_distance(float x1, float y1, float x2, float y2) {
    float dx = x1 - x2;
    float dy = y1 - y2;
    return std::sqrt(dx*dx + dy*dy);
}

// Batch collision detection for power-ups
std::vector<bool> check_player_powerup_collisions(
    const std::vector<float>& player,
    const std::vector<std::vector<float>>& powerups,
    float player_w, float player_h,
    float powerup_w, float powerup_h) {
    
    std::vector<bool> collisions(powerups.size(), false);
    Rect player_rect(player[0], player[1], player_w, player_h);
    
    for (size_t i = 0; i < powerups.size(); ++i) {
        Rect pu(powerups[i][0], powerups[i][1], powerup_w, powerup_h);
        
        if (player_rect.collides_with(pu)) {
            collisions[i] = true;
        }
    }
    
    return collisions;
}

PYBIND11_MODULE(game_accelerator, m) {
    m.def("check_bullet_enemy_collisions", &check_bullet_enemy_collisions,
        "Fast bullet-enemy collision detection");
    
    m.def("check_player_enemy_collisions", &check_player_enemy_collisions,
        "Fast player-enemy collision detection");
    
    m.def("calculate_landmark_distance", &calculate_landmark_distance,
        "Calculate distance between two 3D points");
    
    m.def("is_pinch_detected", &is_pinch_detected,
        "Check if pinch gesture is detected");
    
    m.def("map_finger_position", &map_finger_position,
        "Map normalized finger position to screen coordinates");
    
    m.def("update_enemy_positions", &update_enemy_positions,
        "Update all enemy positions");
    
    m.def("calculate_aim_direction", &calculate_aim_direction,
        "Calculate aim direction for enemy shots");
    
    m.def("bullet_boss_collision", &bullet_boss_collision,
        "Check bullet-boss collision");
    
    m.def("player_bullet_collision", &player_bullet_collision,
        "Check player-bullet collision");
    
    m.def("point_distance", &point_distance,
        "Calculate distance between two 2D points");
    
    m.def("check_player_powerup_collisions", &check_player_powerup_collisions,
        "Check player-powerup collisions");
}
