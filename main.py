# main.py
# Trust Issues (Pygame)
# Handles: level building, restarting, menu, and basic progression.

from __future__ import annotations
import pygame as pg

from settings import WIDTH, HEIGHT, FPS, TITLE, BG, WHITE, ACCENT
from entities import (
    Player, Camera,
    Platform, FakePlatform, InvisiblePlatform, FallingPlatform, MovingPlatform, ConveyorPlatform, BouncePlatform,
    Spike, SlidingSpike, FallingSpike, RisingSpike,
    Goal, Sign,
    TriggerZone, ControlZone,
)
from level_data import build_levels, mirror_level


DEV_MODE = True


def _rect_copy(r):
    return r.copy() if isinstance(r, pg.Rect) else pg.Rect(r)


def clone_level_def(d: dict) -> dict:
    # Make fresh Rects so a restarted level doesn't keep moved trap positions.
    out = dict(d)

    out["spawn"] = tuple(d["spawn"])
    out["world"] = tuple(d["world"])
    out["goal"] = _rect_copy(d["goal"])

    plats = []
    for item in d.get("platforms", []):
        kind = item[0]

        if kind in ("solid", "fake", "falling", "invisible"):
            _, rect = item
            plats.append((kind, _rect_copy(rect)))

        elif kind == "moving":
            _, (rect, a, b, speed) = item
            plats.append((kind, (_rect_copy(rect), tuple(a), tuple(b), speed)))

        elif kind == "conveyor":
            _, payload = item
            rect, speed = payload[0], payload[1]
            if len(payload) >= 3:
                plats.append((kind, (_rect_copy(rect), speed, payload[2])))
            else:
                plats.append((kind, (_rect_copy(rect), speed)))

        elif kind == "bounce":
            _, (rect, strength) = item
            plats.append((kind, (_rect_copy(rect), strength)))

        else:
            plats.append(item)

    out["platforms"] = plats

    out["spikes"] = [_rect_copy(r) for r in d.get("spikes", [])]
    out["sliding_spikes"] = [(_rect_copy(r), tuple(v)) for (r, v) in d.get("sliding_spikes", [])]
    out["falling_spikes"] = [(_rect_copy(r), spd) for (r, spd) in d.get("falling_spikes", [])]
    out["rising_spikes"] = [(_rect_copy(r), spd) for (r, spd) in d.get("rising_spikes", [])]

    out["signs"] = [(_rect_copy(r), text) for (r, text) in d.get("signs", [])]
    out["triggers"] = [(name, _rect_copy(r)) for (name, r) in d.get("triggers", [])]
    out["control_zones"] = [_rect_copy(r) for r in d.get("control_zones", [])]

    out["rules"] = dict(d.get("rules", {}))
    out["goal_rules"] = dict(d.get("goal_rules", {}))
    return out


class Level:
    def __init__(self, level_def: dict, mirrored: bool = False):
        level_def = clone_level_def(level_def)

        self.defn = level_def
        self.name = level_def["name"] + (" [MIRRORED]" if mirrored else "")
        self.world_w, self.world_h = level_def["world"]

        sx, sy = level_def["spawn"]
        self.player = Player(sx, sy)

        # object lists (updated/drawn each frame)
        self.platforms: list = []
        self.spikes: list[Spike] = []
        self.sliding_spikes: list[SlidingSpike] = []
        self.falling_spikes: list[FallingSpike] = []
        self.rising_spikes: list[RisingSpike] = []

        self.signs: list[Sign] = []
        self.triggers: list[TriggerZone] = []
        self.control_zones: list[ControlZone] = []

        # control gimmick
        self.controls_inverted = False
        self._invert_forced = False

        # small on-screen message
        self.msg = ""
        self.msg_t = 0.0

        self.camera = Camera(self.world_w, self.world_h)
        self._goal_reset_done = False

        rules = level_def.get("rules", {})
        self.ground_spikes_arm_on_jump = rules.get("ground_spikes_arm_on_jump", False)
        self.jump_trap_sequence = rules.get("jump_trap_sequence", False)
        self._jump_trap_index = 0

        self._build(level_def)

        if self.ground_spikes_arm_on_jump:
            for s in self.spikes:
                s.active = False

    def _build(self, d: dict):
        # Platforms
        for item in d["platforms"]:
            kind = item[0]

            if kind == "solid":
                _, rect = item
                self.platforms.append(Platform(rect))
            elif kind == "fake":
                _, rect = item
                self.platforms.append(FakePlatform(rect))
            elif kind == "falling":
                _, rect = item
                self.platforms.append(FallingPlatform(rect))
            elif kind == "invisible":
                _, rect = item
                self.platforms.append(InvisiblePlatform(rect))
            elif kind == "moving":
                _, (rect, a, b, speed) = item
                self.platforms.append(MovingPlatform(rect, a, b, speed))
            elif kind == "conveyor":
                _, payload = item
                rect, speed = payload[0], payload[1]
                boost = payload[2] if len(payload) >= 3 else 1.0
                self.platforms.append(ConveyorPlatform(rect, speed, boost=boost))
            elif kind == "bounce":
                _, (rect, strength) = item
                self.platforms.append(BouncePlatform(rect, strength=strength))

        # Hazards
        for rect in d.get("spikes", []):
            self.spikes.append(Spike(rect, active=True))

        for rect, vel in d.get("sliding_spikes", []):
            self.sliding_spikes.append(SlidingSpike(rect, vel))

        for rect, speed in d.get("falling_spikes", []):
            self.falling_spikes.append(FallingSpike(rect, drop_speed=speed))

        for rect, speed in d.get("rising_spikes", []):
            self.rising_spikes.append(RisingSpike(rect, rise_speed=speed))

        # Signs / zones
        for rect, text in d.get("signs", []):
            self.signs.append(Sign(rect, text))

        for z in d.get("control_zones", []):
            self.control_zones.append(ControlZone(z))

        # Triggers are small “if player enters rect, do something once” zones
        for name, rect in d.get("triggers", []):
            if name == "INVERT_ON":
                def inv_on(level):
                    level._invert_forced = True
                    level.flash_msg("NOPE (controls).", 0.8)
                self.triggers.append(TriggerZone(rect, inv_on, once=True))

            elif name == "INVERT_OFF":
                def inv_off(level):
                    level._invert_forced = False
                    level.flash_msg("Okay fine.", 0.7)
                self.triggers.append(TriggerZone(rect, inv_off, once=True))

            elif name == "DROP_SPIKES":
                def drop_spikes(level):
                    for fs in level.falling_spikes:
                        fs.trigger(level)
                    level.flash_msg("Too late.", 0.8)
                self.triggers.append(TriggerZone(rect, drop_spikes, once=True))

            elif name == "SLIDE_SPIKES":
                def slide_spikes(level):
                    for ss in level.sliding_spikes:
                        ss.trigger(level)
                    level.flash_msg("RUN.", 0.7)
                self.triggers.append(TriggerZone(rect, slide_spikes, once=True))

        # Goal (door)
        self.goal = Goal(d["goal"])
        gr = d.get("goal_rules", {})
        if gr.get("run_away", False):
            self.goal.run_away = True
        if "teleport_once" in gr:
            self.goal.teleport_once = True
            self.goal.teleport_to = gr["teleport_once"]
        if "patrol" in gr:
            x1, x2, spd = gr["patrol"]
            y = self.goal.rect.y
            self.goal.patrol = True
            self.goal.patrol_a = (x1, y)
            self.goal.patrol_b = (x2, y)
            self.goal.patrol_speed = spd

    def flash_msg(self, text: str, t: float = 1.0):
        self.msg = text
        self.msg_t = t

    def on_player_jump(self):
        # Some levels arm ground spikes only after the first jump.
        if self.ground_spikes_arm_on_jump:
            for s in self.spikes:
                s.active = True

        # Some levels trigger traps based on jump count.
        if not self.jump_trap_sequence:
            return

        trap_every = self.defn.get("rules", {}).get("trap_every_jump", False)
        px = self.player.rect.centerx + int(self.player.vel.x * 0.10)

        nf = len(self.falling_spikes)
        nr = len(self.rising_spikes)
        if nf == 0 and nr == 0:
            return

        if trap_every:
            cycle_len = nf + nr
            idx = self._jump_trap_index % cycle_len

            if idx < nf:
                self.falling_spikes[idx].trigger(self, px)
            else:
                rs = self.rising_spikes[idx - nf]
                rs.rect.centerx = px
                rs.rect.x = max(0, min(rs.rect.x, self.world_w - rs.rect.w))
                rs.trigger(self)

            self._jump_trap_index += 1
            return

        i = self._jump_trap_index
        if i == 0 and nf >= 1:
            self.falling_spikes[0].trigger(self, px)
        elif i == 1 and nf >= 2:
            self.falling_spikes[1].trigger(self, px)
        elif i == 2 and nr >= 1:
            rs = self.rising_spikes[0]
            rs.rect.centerx = px
            rs.rect.x = max(0, min(rs.rect.x, self.world_w - rs.rect.w))
            rs.trigger(self)

        self._jump_trap_index += 1

    def handle_goal_touch(self) -> bool:
        # This lets a level “troll” once: teleport the door, spawn spikes, etc.
        gr = self.defn.get("goal_rules", {})

        if gr.get("reset_on_touch", False) and (not self._goal_reset_done):
            self._goal_reset_done = True

            to = gr.get("reset_to")
            if to:
                self.goal.rect.topleft = to
                self.flash_msg("The exit moved. Obviously.", 1.1)

            for x, y, w, h in gr.get("add_spikes", []):
                self.spikes.append(Spike(pg.Rect(x, y, w, h), active=True))

            return False

        return True

    def update(self, dt: float, keys):
        # Message timer
        if self.msg_t > 0:
            self.msg_t -= dt
            if self.msg_t <= 0:
                self.msg = ""

        # Control zones invert movement while inside
        zone_inv = any(z.rect.colliderect(self.player.rect) for z in self.control_zones)
        self.controls_inverted = self._invert_forced or zone_inv

        # Update platforms first (moving platforms need to move before player collision)
        for p in self.platforms:
            p.update(dt, self)
        self.platforms = [p for p in self.platforms if not p.dead]

        self.player.update(dt, keys, self)

        # When dead: show death screen, restart only with R (handled in main loop)
        if self.player.dead:
            return

        # Hazards
        for s in self.spikes:
            s.check(self.player)

        for s in self.sliding_spikes:
            s.update(dt, self)
            s.check(self.player)

        for fs in self.falling_spikes:
            fs.update(dt, self)
            fs.check(self.player)

        for rs in self.rising_spikes:
            rs.update(dt, self)
            rs.check(self.player)

        # Trigger zones
        for tz in self.triggers:
            tz.update(self)

        # Goal + camera
        self.goal.update(dt, self)
        self.camera.update(self.player.rect, WIDTH, HEIGHT)

    def draw(self, screen: pg.Surface, font_big, font_small):
        screen.fill(BG)

        for p in self.platforms:
            p.draw(screen, self.camera)

        for s in self.spikes:
            s.draw(screen, self.camera)
        for s in self.sliding_spikes:
            s.draw(screen, self.camera)
        for s in self.falling_spikes:
            s.draw(screen, self.camera)
        for s in self.rising_spikes:
            s.draw(screen, self.camera)

        self.goal.draw(screen, self.camera)

        for sign in self.signs:
            sign.draw(screen, self.camera, font_small)

        self.player.draw(screen, self.camera)

        screen.blit(font_small.render(self.name, True, (210, 210, 210)), (16, 12))

        if self.controls_inverted:
            screen.blit(font_small.render("CONTROLS INVERTED", True, (255, 160, 160)), (16, 92))

        if self.player.dead:
            m1 = font_big.render("YOU DIED", True, (255, 95, 110))
            screen.blit(m1, (WIDTH // 2 - m1.get_width() // 2, HEIGHT // 2 - 80))
            m2 = font_small.render(self.player.death_reason, True, WHITE)
            screen.blit(m2, (WIDTH // 2 - m2.get_width() // 2, HEIGHT // 2 - 30))
            m3 = font_small.render("Press R to retry", True, ACCENT)
            screen.blit(m3, (WIDTH // 2 - m3.get_width() // 2, HEIGHT // 2 + 10))

        if self.msg:
            m = font_small.render(self.msg, True, ACCENT)
            screen.blit(m, (WIDTH // 2 - m.get_width() // 2, 120))


class LevelManager:
    def __init__(self):
        self.base_levels = build_levels()
        self.mirrored = False

        self.unlocked = len(self.base_levels) if DEV_MODE else 1

        self.index = 0
        self.levels = self.base_levels
        self.level = Level(self.levels[self.index], mirrored=self.mirrored)

    def set_mode(self, mirrored: bool):
        self.mirrored = mirrored
        self.levels = [mirror_level(l) for l in self.base_levels] if mirrored else self.base_levels
        self.index = max(0, min(self.index, len(self.levels) - 1))
        self.level = Level(self.levels[self.index], mirrored=self.mirrored)

    def select_level(self, idx: int):
        self.index = idx
        self.level = Level(self.levels[self.index], mirrored=self.mirrored)

    def restart_level(self):
        self.level = Level(self.levels[self.index], mirrored=self.mirrored)

    def mark_completed(self):
        if self.unlocked < self.index + 2:
            self.unlocked = self.index + 2

    def can_play(self, idx: int) -> bool:
        if DEV_MODE:
            return True
        return (idx + 1) <= self.unlocked

    def next_level(self) -> bool:
        nxt = self.index + 1
        if nxt >= len(self.levels):
            return False
        if not self.can_play(nxt):
            return False
        self.select_level(nxt)
        return True


def draw_center(screen, font, text, y, color):
    img = font.render(text, True, color)
    screen.blit(img, (WIDTH // 2 - img.get_width() // 2, y))


def main():
    pg.init()
    pg.display.set_caption(TITLE)
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    clock = pg.time.Clock()

    font_big = pg.font.SysFont("consolas", 52, bold=True)
    font_small = pg.font.SysFont("consolas", 22, bold=True)

    mgr = LevelManager()
    state = "select"

    while True:
        dt = clock.tick(FPS) / 1000.0
        keys = pg.key.get_pressed()

        for e in pg.event.get():
            if e.type == pg.QUIT:
                raise SystemExit

            if e.type == pg.KEYDOWN:
                if state == "select":
                    if e.key == pg.K_m:
                        mgr.set_mode(not mgr.mirrored)

                    if pg.K_1 <= e.key <= pg.K_9:
                        idx = e.key - pg.K_1
                        if idx < len(mgr.levels) and mgr.can_play(idx):
                            mgr.select_level(idx)
                            state = "play"

                    if e.key == pg.K_0:
                        idx = 9
                        if idx < len(mgr.levels) and mgr.can_play(idx):
                            mgr.select_level(idx)
                            state = "play"

                    if e.key == pg.K_F1:
                        idx = 10
                        if idx < len(mgr.levels) and mgr.can_play(idx):
                            mgr.select_level(idx)
                            state = "play"

                    if e.key == pg.K_F2:
                        idx = 11
                        if idx < len(mgr.levels) and mgr.can_play(idx):
                            mgr.select_level(idx)
                            state = "play"

                elif state == "play":
                    if e.key == pg.K_r:
                        mgr.restart_level()
                        continue
                    if e.key == pg.K_ESCAPE:
                        state = "select"

                elif state == "complete":
                    if e.key == pg.K_n:
                        state = "play" if mgr.next_level() else "select"
                    elif e.key == pg.K_r:
                        mgr.restart_level()
                        state = "play"
                    elif e.key == pg.K_ESCAPE:
                        state = "select"

        if state == "select":
            screen.fill((10, 10, 14))
            draw_center(screen, font_big, "TRUST ISSUES", 80, ACCENT)
            draw_center(screen, font_small, "Pick level: 1-9, 0=10, F1=11, F2=12", 140, (200, 200, 200))
            draw_center(screen, font_small, f"Mode: {'MIRRORED' if mgr.mirrored else 'NORMAL'}  (press M)", 170, (170, 170, 170))

            y = 240
            for i, lv in enumerate(mgr.base_levels):
                unlocked = mgr.can_play(i)
                lock = "" if unlocked else "  [LOCKED]"
                label = f"{i+1:02d}. {lv['name']}{lock}"
                color = (230, 230, 230) if unlocked else (90, 90, 95)
                screen.blit(font_small.render(label, True, color), (110, y))
                y += 26

            screen.blit(font_small.render("Esc returns here", True, (150, 150, 150)), (110, HEIGHT - 70))
            pg.display.flip()
            continue

        if state == "play":
            mgr.level.update(dt, keys)

            if (not mgr.level.player.dead) and mgr.level.goal.reached(mgr.level.player):
                mgr.level.goal.on_touch(mgr.level)
                if mgr.level.handle_goal_touch():
                    mgr.mark_completed()
                    state = "complete"

            mgr.level.draw(screen, font_big, font_small)
            pg.display.flip()
            continue

        if state == "complete":
            screen.fill((10, 10, 14))
            draw_center(screen, font_big, "LEVEL COMPLETE", HEIGHT // 2 - 140, (110, 255, 170))
            draw_center(screen, font_small, "N = Next   R = Retry   Esc = Level Select", HEIGHT // 2 - 40, (220, 220, 220))
            pg.display.flip()
            continue


if __name__ == "__main__":
    main()
