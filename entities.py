# entities.py
# Game objects: player, platforms, hazards, goal, and small helper zones.

from __future__ import annotations

import math
import pygame as pg

from settings import (
    GRAVITY, PLAYER_SPEED, PLAYER_JUMP, FRICTION,
    COYOTE_TIME, JUMP_BUFFER,
    WHITE, ACCENT, RED, GREEN, CYAN, PURPLE, DARK
)

Vec2 = pg.math.Vector2


#
# Camera
#
# Keeps the player centered while staying inside the level bounds.

class Camera:
    def __init__(self, world_w: int, world_h: int):
        self.world_w = world_w
        self.world_h = world_h
        self.offset = Vec2(0, 0)

    def update(self, target_rect: pg.Rect, screen_w: int, screen_h: int):
        # Follow player
        x = target_rect.centerx - screen_w // 2
        y = target_rect.centery - screen_h // 2
        # Clamp to world
        x = max(0, min(x, self.world_w - screen_w))
        y = max(0, min(y, self.world_h - screen_h))
        self.offset.update(x, y)

    def apply(self, rect: pg.Rect) -> pg.Rect:
        # World -> screen coordinates
        return rect.move(-int(self.offset.x), -int(self.offset.y))


# 
# Player

class Player:
    def __init__(self, x: int, y: int):
        self.rect = pg.Rect(x, y, 30, 60)
        self.spawn = Vec2(x, y)
        self.vel = Vec2(0, 0)

        self.dead = False
        self.death_reason = ""

        # Jump helpers (makes jumping feel less strict)
        self.coyote_t = 0.0
        self.jump_buffer_t = 0.0

        self.on_ground = False
        self.ground_obj = None  # platform object the player is standing on

    def respawn(self):
        # Full state reset (used when reloading a level, or if you ever add checkpoints)
        self.rect.topleft = (int(self.spawn.x), int(self.spawn.y))
        self.vel.update(0, 0)
        self.dead = False
        self.death_reason = ""
        self.coyote_t = 0.0
        self.jump_buffer_t = 0.0
        self.on_ground = False
        self.ground_obj = None

    def kill(self, reason: str):
        self.dead = True
        self.death_reason = reason

    def update(self, dt: float, keys, level):
        if self.dead:
            return

        # Controls
        left = keys[pg.K_a] or keys[pg.K_LEFT]
        right = keys[pg.K_d] or keys[pg.K_RIGHT]
        jump = keys[pg.K_SPACE] or keys[pg.K_w] or keys[pg.K_UP]

        # Levels can invert left/right
        if level.controls_inverted:
            left, right = right, left

        move = (1 if right else 0) - (1 if left else 0)

        # Smooth horizontal movement
        target = move * PLAYER_SPEED
        self.vel.x += (target - self.vel.x) * min(1.0, 12.0 * dt)

        # Friction when no input
        if move == 0:
            self.vel.x *= (1.0 - min(1.0, FRICTION * dt))

        # Jump buffer (press slightly early still counts)
        if jump:
            self.jump_buffer_t = JUMP_BUFFER
        else:
            self.jump_buffer_t = max(0.0, self.jump_buffer_t - dt)

        # Gravity
        self.vel.y += GRAVITY * dt

        # Coyote time (jump slightly late still counts)
        if self.on_ground:
            self.coyote_t = COYOTE_TIME
        else:
            self.coyote_t = max(0.0, self.coyote_t - dt)

        # Jump
        if self.jump_buffer_t > 0 and self.coyote_t > 0:
            self.vel.y = -PLAYER_JUMP
            self.jump_buffer_t = 0.0
            self.coyote_t = 0.0
            level.on_player_jump()

        # Movement + collision
        self._move_and_collide(dt, level)

        # Carry the player with moving platforms (so you don't slip off)
        if self.on_ground and self.ground_obj is not None and hasattr(self.ground_obj, "delta"):
            self.rect.x += int(self.ground_obj.delta.x)
            self.rect.y += int(self.ground_obj.delta.y)

        # Conveyor belt pushes you while grounded
        if self.on_ground and isinstance(self.ground_obj, ConveyorPlatform):
            self.rect.x += int(self.ground_obj.speed * self.ground_obj.boost * dt)

        # Fall out of the level
        if self.rect.top > level.world_h + 350:
            self.kill("Fell into the void.")

    def _move_and_collide(self, dt: float, level):
        # --- X axis ---
        self.rect.x += int(self.vel.x * dt)
        for p in level.platforms:
            # Some platforms react just by touching (fake platforms)
            p.on_player_touch(level, self)

            if p.solid and self.rect.colliderect(p.rect):
                if self.vel.x > 0:
                    self.rect.right = p.rect.left
                elif self.vel.x < 0:
                    self.rect.left = p.rect.right
                self.vel.x = 0

        # ---Y axis--- 
        self.rect.y += int(self.vel.y * dt)
        self.on_ground = False
        self.ground_obj = None

        for p in level.platforms:
            p.on_player_touch(level, self)
            if not p.solid:
                continue

            if self.rect.colliderect(p.rect):
                if self.vel.y > 0:
                    # landing
                    self.rect.bottom = p.rect.top
                    self.vel.y = 0
                    self.on_ground = True
                    self.ground_obj = p
                    p.on_player_land(level, self)
                elif self.vel.y < 0:
                    # head bump
                    self.rect.top = p.rect.bottom
                    self.vel.y = 0

    def draw(self, surf: pg.Surface, cam: Camera):
        # Stick figure with small arm/leg animation
        r = cam.apply(self.rect)

        facing = 1 if self.vel.x >= 0 else -1
        speed = abs(self.vel.x)
        moving = speed > 30
        t = pg.time.get_ticks() / 1000.0

        freq = 8 + (min(speed, 360) / 360) * 10
        swing = 0.0
        bob = 0.0
        if moving and self.on_ground:
            swing = 10 * math.sin(t * freq)
            bob = 2 * math.sin(t * freq)

        cx = r.centerx
        head_r = 9
        head_y = int(r.y + head_r + 4 + bob)
        body_top = head_y + head_r
        body_bottom = int(r.bottom - 6 + bob)

        pg.draw.circle(surf, WHITE, (cx, head_y), head_r, 2)
        pg.draw.line(
            surf, WHITE,
            (cx + facing * head_r, head_y),
            (cx + facing * (head_r + 6), head_y),
            2
        )

        pg.draw.line(surf, WHITE, (cx, body_top), (cx, body_bottom), 3)

        arm_y = body_top + 12
        pg.draw.line(surf, WHITE, (cx, arm_y), (cx + facing * 14, arm_y + int(swing * 0.3)), 3)
        pg.draw.line(surf, WHITE, (cx, arm_y), (cx - facing * 12, arm_y - int(swing * 0.2)), 2)

        leg_base = body_bottom
        pg.draw.line(surf, WHITE, (cx, leg_base), (cx + facing * (10 + int(swing)), r.bottom), 3)
        pg.draw.line(surf, WHITE, (cx, leg_base), (cx - facing * (8 + int(swing * 0.6)), r.bottom), 2)


# 
# Platforms
class Platform:
    # Base platform. Most platform types just change update/on_land logic.
    def __init__(self, rect: pg.Rect, color=DARK, solid=True):
        self.rect = rect
        self.color = color
        self.solid = solid
        self.dead = False  # removed from the list when True

    def on_player_touch(self, level, player: Player):
        pass

    def on_player_land(self, level, player: Player):
        pass

    def update(self, dt: float, level):
        pass

    def draw(self, surf: pg.Surface, cam: Camera):
        r = cam.apply(self.rect)
        pg.draw.rect(surf, self.color, r, border_radius=10)
        pg.draw.rect(surf, (90, 92, 110), r, width=2, border_radius=10)


class FakePlatform(Platform):
    # Turns off after a short delay 
    def __init__(self, rect: pg.Rect, delay=0.1):
        super().__init__(rect, PURPLE, solid=True)
        self.delay = delay
        self.triggered = False

    def on_player_land(self, level, player: Player):
        if not self.triggered:
            self.triggered = True
            level.flash_msg("Purple = liar.", 0.8)

    def on_player_touch(self, level, player: Player):
        # Some cases touch triggers it even if you don't fully land
        if (not self.triggered) and self.rect.colliderect(player.rect):
            self.triggered = True
            level.flash_msg("Purple = liar.", 0.8)

    def update(self, dt: float, level):
        if self.triggered:
            self.delay -= dt
            if self.delay <= 0:
                self.dead = True
                self.solid = False


class InvisiblePlatform(Platform):
    # Solid platform that does not draw
    def __init__(self, rect: pg.Rect):
        super().__init__(rect, color=(60, 60, 80), solid=True)

    def draw(self, surf: pg.Surface, cam: Camera):
        return


class FallingPlatform(Platform):
    # Falls once the player stands on it
    def __init__(self, rect: pg.Rect, fall_delay=0.18):
        super().__init__(rect, CYAN, solid=True)
        self.armed = False
        self.delay = fall_delay
        self.vy = 0.0

    def on_player_land(self, level, player: Player):
        self.armed = True

    def update(self, dt: float, level):
        if self.armed:
            self.delay -= dt
            if self.delay <= 0:
                self.vy += 2600 * dt
                self.rect.y += int(self.vy * dt)
                if self.rect.top > level.world_h + 450:
                    self.dead = True


class MovingPlatform(Platform):
    # Moves back and forth between point A and point B
    def __init__(self, rect: pg.Rect, a, b, speed=160.0):
        super().__init__(rect, color=(255, 180, 80), solid=True)
        self.a = Vec2(a)
        self.b = Vec2(b)
        self.speed = speed
        self.dir = 1
        self.delta = Vec2(0, 0)  # how much it moved this frame

    def update(self, dt: float, level):
        old = Vec2(self.rect.topleft)

        target = self.b if self.dir == 1 else self.a
        pos = Vec2(self.rect.topleft)
        d = target - pos
        dist = d.length()

        if dist < 1:
            self.dir *= -1
            self.delta.update(0, 0)
            return

        d.normalize_ip()
        step = min(dist, self.speed * dt)
        pos += d * step
        self.rect.topleft = (int(pos.x), int(pos.y))

        new = Vec2(self.rect.topleft)
        self.delta = new - old


class ConveyorPlatform(Platform):
    # Pushes the player sideways while standing on it
    def __init__(self, rect: pg.Rect, speed: float, boost: float = 1.0):
        super().__init__(rect, color=(120, 220, 255), solid=True)
        self.speed = speed
        self.boost = boost

    def draw(self, surf: pg.Surface, cam: Camera):
        # Same platform look but with arrows
        r = cam.apply(self.rect)
        pg.draw.rect(surf, self.color, r, border_radius=10)
        pg.draw.rect(surf, WHITE, r, 2, border_radius=10)
        for x in range(r.left + 12, r.right - 12, 28):
            pg.draw.polygon(
                surf, (30, 30, 40),
                [(x, r.centery),
                 (x + (10 if self.speed > 0 else -10), r.centery - 6),
                 (x + (10 if self.speed > 0 else -10), r.centery + 6)]
            )


class BouncePlatform(Platform):
    # Sets player horizontal velocity on landing (launch pad)
    def __init__(self, rect: pg.Rect, strength: float = 900.0):
        super().__init__(rect, color=(255, 180, 80), solid=True)
        self.strength = strength

    def on_player_land(self, level, player: Player):
        # Note: negative strength launches to the right (because of the minus sign here)
        player.vel.x = -self.strength
        level.flash_msg("NOPE.", 0.7)


#
# Spikes / Traps

class Spike:
    def __init__(self, rect: pg.Rect, active=True):
        self.rect = rect
        self.active = active

    def check(self, player: Player):
        if self.active and self.rect.colliderect(player.rect):
            player.kill("Spikes.")

    def draw(self, surf: pg.Surface, cam: Camera):
        # Triangle spikes
        if not self.active:
            return
        r = cam.apply(self.rect)
        count = max(1, r.width // 16)
        w = r.width / count
        for i in range(count):
            x0 = r.left + i * w
            x1 = x0 + w
            mid = (x0 + x1) / 2
            pg.draw.polygon(surf, RED, [(x0, r.bottom), (x1, r.bottom), (mid, r.top)])
        pg.draw.rect(surf, (255, 220, 220), r, 1)


class SlidingSpike(Spike):
    # Moves when triggered (usually by a trigger zone)
    def __init__(self, rect: pg.Rect, vel):
        super().__init__(rect, active=True)
        self.vel = Vec2(vel)
        self.triggered = False

    def trigger(self, level):
        self.triggered = True
        level.flash_msg("RUN.", 0.7)

    def update(self, dt: float, level):
        if self.triggered:
            self.rect.x += int(self.vel.x * dt)
            self.rect.y += int(self.vel.y * dt)


class FallingSpike(Spike):
    # Drops down once triggered
    def __init__(self, rect: pg.Rect, drop_speed=1200.0):
        super().__init__(rect, active=True)
        self.drop_speed = drop_speed
        self.triggered = False
        self.start_y = rect.y  # used so it can reset to its start height

    def trigger(self, level, target_x: int | None = None):
        # Reset to start Y each time, then activate
        self.rect.y = self.start_y
        self.triggered = True

        # Optional: align above the player
        if target_x is not None:
            self.rect.centerx = target_x

        # Clamp inside the world
        self.rect.x = max(0, min(self.rect.x, level.world_w - self.rect.w))

    def update(self, dt: float, level):
        if self.triggered:
            self.rect.y += int(self.drop_speed * dt)


class RisingSpike(Spike):
    # Shoots up once triggered
    def __init__(self, rect: pg.Rect, rise_speed=1400.0):
        super().__init__(rect, active=True)
        self.rise_speed = rise_speed
        self.triggered = False

    def trigger(self, level):
        self.triggered = True

    def update(self, dt: float, level):
        if self.triggered:
            self.rect.y -= int(self.rise_speed * dt)

#
# Goal + UI helpers

class Goal:
    def __init__(self, rect: pg.Rect):
        self.rect = rect
        self.run_away = False

        self.teleport_once = False
        self.teleport_to = None
        self._did_tp = False

        self.patrol = False
        self.patrol_a = None
        self.patrol_b = None
        self.patrol_speed = 0.0
        self._patrol_dir = 1

    def reached(self, player: Player) -> bool:
        return self.rect.colliderect(player.rect)

    def on_touch(self, level):
        # Some levels use "teleport_once" (door moves once)
        if self.teleport_once and (not self._did_tp) and self.teleport_to is not None:
            self.rect.topleft = self.teleport_to
            self._did_tp = True
            level.flash_msg("Where did it go?!", 1.0)

        # Some levels use "run_away" (door backs off when touched)
        if self.run_away:
            self.rect.x -= 220
            self.rect.x = max(0, min(self.rect.x, level.world_w - self.rect.w))
            level.flash_msg("Come back here.", 0.8)

    def update(self, dt: float, level):
        # Optional patrol movement (back and forth)
        if self.patrol and self.patrol_a and self.patrol_b:
            a = Vec2(self.patrol_a)
            b = Vec2(self.patrol_b)
            target = b if self._patrol_dir == 1 else a
            pos = Vec2(self.rect.topleft)
            d = target - pos
            if d.length() < 2:
                self._patrol_dir *= -1
            else:
                d.normalize_ip()
                pos += d * (self.patrol_speed * dt)
                self.rect.topleft = (int(pos.x), int(pos.y))

    def draw(self, surf: pg.Surface, cam: Camera):
        r = cam.apply(self.rect)
        pg.draw.rect(surf, GREEN, r, border_radius=14)
        pg.draw.rect(surf, WHITE, r, 2, border_radius=14)


class Sign:
    def __init__(self, rect: pg.Rect, text: str):
        self.rect = rect
        self.text = text

    def draw(self, surf: pg.Surface, cam: Camera, font):
        r = cam.apply(self.rect)
        pg.draw.rect(surf, (35, 35, 45), r, border_radius=10)
        pg.draw.rect(surf, (90, 90, 105), r, 2, border_radius=10)
        y = r.top + 8
        for line in self.text.split("\n"):
            img = font.render(line, True, (230, 230, 230))
            surf.blit(img, (r.left + 10, y))
            y += img.get_height() + 2


class TriggerZone:
    # Rectangle zone that runs a function when the player enters it.
    def __init__(self, rect: pg.Rect, fn, once=True):
        self.rect = rect
        self.fn = fn
        self.once = once
        self.used = False

    def update(self, level):
        if self.used and self.once:
            return
        if self.rect.colliderect(level.player.rect):
            self.fn(level)
            if self.once:
                self.used = True


class ControlZone:
    # Used for inverted controls while inside the zone.
    def __init__(self, rect: pg.Rect):
        self.rect = rect
