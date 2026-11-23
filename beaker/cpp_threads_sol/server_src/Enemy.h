#ifndef TALLER_ENEMY_H
#define TALLER_ENEMY_H

#define ENEMY_REVIVE_TIME 15

class Enemy {
private:
    int revive_cool_down;
    bool alive;

public:
    Enemy();

    bool try_revive();
    void die();
    bool is_alive();

    ~Enemy();
};


#endif  // TALLER_ENEMY_H
