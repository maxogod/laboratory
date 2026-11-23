#include "Enemy.h"

Enemy::Enemy(): revive_cool_down(ENEMY_REVIVE_TIME), alive(true) {}

bool Enemy::try_revive() {
    if (is_alive()) {
        return false;
    }
    this->revive_cool_down--;
    if (this->revive_cool_down == 0) {
        this->alive = true;
        this->revive_cool_down = ENEMY_REVIVE_TIME;
        return true;
    }
    return false;
}

void Enemy::die() { this->alive = false; }

bool Enemy::is_alive() { return this->alive; }

Enemy::~Enemy() = default;
