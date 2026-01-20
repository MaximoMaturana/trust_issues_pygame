# level_data.py
from __future__ import annotations
import pygame as pg


def R(x, y, w, h):
    return pg.Rect(x, y, w, h)


def build_levels():
    levels = []

    def floor_segments(world_w, y=780, h=120, pits=None):
        segs = []
        if not pits:
            return [("solid", R(0, y, world_w, h))]
        pits = sorted(pits)
        start = 0
        for a, b in pits:
            if a > start:
                segs.append(("solid", R(start, y, a - start, h)))
            start = b
        if start < world_w:
            segs.append(("solid", R(start, y, world_w - start, h)))
        return segs

    # 
    # Level 1
    levels.append({
        "name": "1: Welcome",
        "world": (2200, 900),
        "spawn": (120, 720),
        "goal": R(2000, 690, 60, 90),
        "platforms": floor_segments(2200) + [
            ("solid", R(420, 680, 220, 30)),
            ("solid", R(780, 600, 220, 30)),
            ("solid", R(1160, 520, 220, 30)),
            ("solid", R(1500, 650, 240, 30)),
        ],
        "spikes": [R(660, 760, 90, 40)],
        "signs": [(R(180, 650, 250, 70), "Reach the exit.\nIt gets worse.")],
        "control_zones": [],
        "triggers": [],
        "sliding_spikes": [],
        "falling_spikes": [],
        "rising_spikes": [],
        "goal_rules": {},
    })

    # 
    # Level 2
    levels.append({
        "name": "2: Trust the Purple (You shouldn't)",
        "world": (2500, 900),
        "spawn": (120, 720),
        "goal": R(2320, 690, 60, 90),
        "platforms": floor_segments(2500) + [
            ("solid", R(520, 650, 240, 30)),
            ("solid", R(880, 580, 240, 30)),
            ("solid", R(1240, 520, 240, 30)),
            ("solid", R(1600, 650, 240, 30)),

            ("fake", R(1850, 720, 140, 24)),
            ("fake", R(2000, 720, 140, 24)),
            ("fake", R(2150, 720, 140, 24)),
        ],
        "spikes": [R(1860, 760, 450, 40)],
        "signs": [(R(980, 650, 420, 70), "Purple platforms are safe.\nSource: trust me bro")],
        "control_zones": [],
        "triggers": [],
        "sliding_spikes": [],
        "falling_spikes": [],
        "rising_spikes": [],
        "goal_rules": {},
    })

    # 
    # Level 3  (jump-triggered traps)
    levels.append({
        "name": "3: Don't Jump",
        "world": (2400, 900),
        "spawn": (120, 720),
        "goal": R(2140, 690, 60, 90),
        "rules": {
            "ground_spikes_arm_on_jump": True,
            "jump_trap_sequence": True,  # one trap per jump (2 falling + 1 rising)
            "trap_every_jump": True,

        },
        "platforms": floor_segments(2400) + [
            ("solid", R(520, 690, 260, 30)),
            ("solid", R(900, 690, 260, 30)),
            ("solid", R(1280, 690, 260, 30)),
            ("solid", R(1660, 690, 260, 30)),
        ],
        "spikes": [
            R(780, 760, 120, 40),
            R(1160, 760, 120, 40),
            R(1540, 760, 120, 40),
        ],
        "falling_spikes": [
            (R(700, 120, 80, 40), 1000),
            (R(1000, 120, 80, 40), 1200),
            (R(1300, 120, 80, 40), 1400),
        ],
        "rising_spikes": [
            (R(1720, 980, 80, 40), 2000),
            (R(1890, 980, 80, 40), 2000)
        ],
        
        
        "signs": [(R(120, 650, 520, 70), "Do NOT jump.\n(It arms traps one by one.)")],
        "control_zones": [],
        "triggers": [],
        "sliding_spikes": [],
        "goal_rules": {},
    })

    # 
    # Level 4 (the exit runs away + new spikes on the way back)
    levels.append({
        "name": "4: The Exit Has Anxiety",
        "world": (2600, 900),
        "spawn": (120, 720),
        "goal": R(2300, 690, 60, 90),
        "platforms": floor_segments(2600) + [
            ("solid", R(520, 640, 240, 30)),
            ("solid", R(940, 560, 240, 50)),
            ("solid", R(1360, 640, 240, 50)),
            ("solid", R(1760, 700, 240, 50)),
            ("solid", R(2060, 700, 240, 50)),
        ],
        "spikes": [R(1200, 760, 120, 40)],
        "signs": [(R(920, 650, 460, 70), "The exit is right there.\nGo get it :)")],
        "control_zones": [],
        "triggers": [],
        "sliding_spikes": [],
        "falling_spikes": [],
        "rising_spikes": [],
        "goal_rules": {
            "reset_on_touch": True,
            "reset_to": (180, 690),
            "add_spikes": [
                (1700, 760, 140, 40),
                (1320, 760, 140, 40),
                (920, 760, 140, 40),
            ],
        },
    })

    # 
    # Level 5 (conveyors + bounce platform)
    levels.append({
        "name": "5: The Floor Is Moving",
        "world": (2700, 900),
        "spawn": (120, 720),
        "goal": R(2460, 690, 60, 90),
        "platforms": floor_segments(2700, pits=[(940, 1120), (1680, 1840)]) + [
            ("conveyor", (R(300, 780, 520, 120), 400, 2.5)),
            ("conveyor", (R(1200, 780, 420, 120), -700, 2)),

            ("falling", R(780, 620, 160, 24)),
            ("falling", R(1060, 620, 160, 24)),
            ("falling", R(1360, 620, 160, 24)),
            ("falling", R(1660, 580, 160, 24)),
            ("falling", R(1960, 40, 160, 24)),

            ("solid", R(520, 700, 260, 30)),
            ("solid", R(2140, 690, 260, 30)),

            ("bounce", (R(1920, 700, 200, 24), 3000)),
        ],
        "spikes": [],
        "signs": [(R(120, 650, 520, 70), "The arrows help you.\n(…or do they?)")],
        "control_zones": [],
        "triggers": [],
        "sliding_spikes": [],
        "falling_spikes": [],
        "rising_spikes": [],
        "goal_rules": {},
    })

    # 
    # Level 6 (inversion you can actually plan for)
    levels.append({
        "name": "6: Inverted Reality",
        "world": (2800, 900),
        "spawn": (120, 720),
        "goal": R(2550, 690, 60, 90),

        "platforms": floor_segments(2800, pits=[(1320, 1500)]) + [
            ("solid", R(520, 650, 260, 30)),
            ("solid", R(920, 600, 260, 30)),

            ("fake", R(1360, 560, 180, 24)),  # purple mid-jump

            ("solid", R(1720, 650, 260, 30)),
            ("solid", R(2100, 700, 260, 30)),
        ],
        "spikes": [R(1500, 760, 200, 40)],
        "signs": [(R(120, 650, 520, 70), "Controls flip… but only until you\npass the spikes.")],
        "control_zones": [],
        "triggers": [
            ("INVERT_ON", R(760, 560, 520, 280)),
            ("INVERT_OFF", R(1720, 520, 520, 320)),
        ],
        "sliding_spikes": [],
        "falling_spikes": [],
        "rising_spikes": [],
        "goal_rules": {},
    })

    # 
    # Level 7 (invisible platforms)
    levels.append({
        "name": "7: Invisible Staircase",
        "world": (2600, 900),
        "spawn": (120, 720),
        "goal": R(2360, 690, 60, 90),
        "platforms": floor_segments(2600, pits=[(880, 1180), (1600, 1800)]) + [
            ("solid", R(520, 700, 260, 30)),
            ("invisible", R(940, 660, 180, 24)),
            ("invisible", R(1160, 600, 180, 24)),
            ("invisible", R(1380, 540, 180, 24)),
            ("solid", R(1960, 700, 260, 30)),
        ],
        "spikes": [R(920, 760, 260, 40)],
        "signs": [(R(120, 650, 520, 70), "Jump where you can't see.\n(Yes, seriously.)")],
        "control_zones": [],
        "triggers": [],
        "sliding_spikes": [],
        "falling_spikes": [],
        "goal_rules": {},
    })

    # 
    # Level 8 (moving platforms section)
    levels.append({
        "name": "8: Moving Platforms (Timing Hell)",
        "world": (3000, 900),
        "spawn": (120, 720),
        "goal": R(2750, 690, 60, 90),
        "platforms": floor_segments(3000, pits=[(920, 1400), (1700, 2120)]) + [
            ("solid", R(700, 700, 150, 30)),
            ("moving", (R(900, 620, 160, 24), (900, 620), (1280, 540), 190)),
            ("moving", (R(1290, 680, 160, 24), (1290, 680), (1600, 620), 210)),
            ("moving", (R(1710, 640, 160, 24), (1710, 640), (2060, 520), 200)),
            ("solid", R(2260, 700, 350, 30)),
        ],
        "spikes": [R(1400, 760, 300, 40)],
        "signs": [(R(120, 650, 200, 70), "Just time it.\n(yeah… sure)")],
        "control_zones": [],
        "triggers": [],
        "sliding_spikes": [],
        "falling_spikes": [],
        "goal_rules": {"patrol": (2600, 2850, 240)},  # patrol exit
    })

    
    #
    # Level 9 (platforms only: falling + fake + bounce)
    levels.append({
        "name": "9: Trust Issues Parkour",
        "world": (3000, 900),
        "spawn": (120, 720),
        "goal": R(2750, 690, 60, 90),

     

        # floor with pits stays (it's part of the "world"), but all challenge platforms are falling/fake/bounce
        "platforms": floor_segments(3000, pits=[(510, 2600)]) + [
            # Warmup fake path
            ("fake",   R(520,  700, 180, 24)),
            ("fake",   R(760,  660, 180, 24)),
         

            # Pit 1: falling staircase over the gap
            ("falling", R(1120, 600, 160, 24)),
            ("falling", R(1280, 560, 160, 24)),
            ("fake",    R(1460, 520, 180, 24)),

           

       
            ("bounce", (R(1840, 700, 200, 24), 1200)),

            # Landing after pit 2
            ("falling", R(2180, 640, 90, 24)),
            ("bounce",    (R(2340, 600, 180, 24), 1200)),
            ("falling", R(2580, 560, 90, 24)),
            
        ],

        # no ground spikes, no ambush traps
        "spikes": [],
        "signs": [(R(120, 650, 560, 70), "Only platforms.\nFalling + Fake + Bounce.\nGood luck :)")],
        "control_zones": [],
        "triggers": [],
        "sliding_spikes": [],
        "falling_spikes": [],
        "rising_spikes": [(R(2600, 760, 1000, 40), 1300)],
        "goal_rules": {},
    })

    #
    # Level 10 (Troll Transform: door teleports + spikes appear + invisible route)
    levels.append({
        "name": "10: The Exit Lied",
        "world": (3200, 900),
        "spawn": (140, 720),

        # Door starts near the end 
        "goal": R(2900, 690, 60, 90),

        "platforms": floor_segments(3200, pits=[(1360, 1540), (2060, 2260)]) + [
            # First run: visible path (fair and doable)
            ("solid",   R(600,  740, 110, 24)),
            ("solid",   R(800,  700, 100, 24)),
            ("fake",    R(990, 610, 150, 24)),  
            ("solid",   R(1230, 580, 150, 24)),   # over pit 1
            ("solid",   R(1560, 560, 200, 24)),
            ("solid",   R(1820, 620, 220, 24)),
            ("fake",    R(2060, 670, 200, 24)),   # over pit 2
            ("solid",   R(2300, 620, 240, 24)),
            ("solid",   R(2580, 580, 240, 24)),
            ("solid",   R(2820, 640, 180, 24)),

            # Second run: invisible path (after door teleports)

            ("invisible", R(2060, 900, 200, 24)),
            ("invisible", R(1200, 670, 450, 24)),
            ("invisible", R(425,  685, 40, 24)),
        ],

        # No spikes at first. Spikes will be added after touching the goal once.
        "spikes": [],

        "signs": [
            (R(160, 570, 620, 80), "Level 10 Tip: The exit is not your friend.\nIf things change... look for what you can't see."),
        ],

        "control_zones": [],
        "triggers": [],
        "sliding_spikes": [],
        "falling_spikes": [],
        "rising_spikes": [],

        # troll logic: touch goal once -> goal teleports + spikes appear ======
        "goal_rules": {
            "reset_on_touch": True,

            # Teleport the exit back near the start.
            # (Place it on the visible ground area, but now the floor will be spiked.)
            "reset_to": (320, 670),

            # Spikes that appear AFTER the first goal touch.
            # These are rectangles (x, y, w, h).
            "add_spikes": [
               
                (0,    860, 1300, 40),
                (520,  764, 260, 28),
                (800,  724, 260, 28),
                (1080, 684, 260, 28),
                (1560, 550, 240, 28),
                (1820, 644, 260, 28),
                (2300, 644, 280, 28),
                (2580, 604, 280, 28),
                (2820, 664, 240, 28),

                # Spike the "teleport area" so you MUST use the invisible step
                (220,  690, 200, 40),
                (464,  690, 75, 40),

                
            ],
        },
    })


    # 
    # Level 11 (mix everything)
    levels.append({
        "name": "11: Mixed Torture",
        "world": (3300, 900),
        "spawn": (120, 720),
        "goal": R(3040, 690, 60, 90),
        "platforms": floor_segments(3300, pits=[(980, 1280), (1450, 1700), (2140, 2350)]) + [
            ("conveyor", (R(300, 780, 480, 120), 500)),
            ("solid", R(520, 650, 260, 30)),
            ("fake", R(1100, 720, 140, 24)),
            ("falling", R(2200, 680, 160, 24)),
            
            ("solid", R(2600, 700, 260, 30)),
        ],
        "spikes": [R(1280, 760, 100, 40)],
        "signs": [(R(120, 650, 520, 70), "If you can beat this, you're ready.")],
        "control_zones": [R(1710, 100, 650, 2000)],
        "triggers": [
            ("DROP_SPIKES", R(2600, 50, 240, 40)),
        ],
        "sliding_spikes": [],
        "falling_spikes": [
            (R(2400, 750, 160, 40), 1050),
            
        ],
        "goal_rules": {"patrol": (2920, 3140, 260)},
    })

    # 
    # Level 12 (final)
    levels.append({
        "name": "12: Final Boss (It’s Just Mean)",
        "world": (3600, 900),
        "spawn": (120, 720),
        "goal": R(3320, 690, 60, 90),       
        "platforms": floor_segments(3600, pits=[(900, 1260), (1460, 1720), (1960, 2280), (2580, 2860)]) + [
            ("solid", R(600, 650, 260, 30)),
            ("moving", (R(980, 640, 160, 24), (980, 640), (1500, 540), 220)),
            ("fake", R(1870, 720, 140, 24)),
            ("fake", R(2010, 720, 140, 24)),
            ("invisible", R(2280, 600, 180, 24)),
            ("moving", (R(2600, 660, 160, 24), (2600, 660), (2750, 600), 240)),
            ("solid", R(3040, 700, 260, 30)),
        ],
        "spikes": [R(1260, 760, 200, 40)],
        "signs": [(R(120, 650, 560, 70), "Last level.\nSurely nothing dumb happens now.")],
        "control_zones": [R(2310, 100, 650, 800)],
        "triggers": [
            ("SLIDE_SPIKES", R(3000, 620, 320, 260)),
            ("DROP_SPIKES", R(1480, 520, 240, 300)),
        ],
        "sliding_spikes": [
            (R(3100, 760, 90, 40), (-1100, 0)),
            (R(3240, 760, 90, 40), (-1200, 0)),
        ],
        "falling_spikes": [
            (R(1560, 720, 80, 40), 1100),
            (R(1660, 720, 80, 40), 1200),
        ],
        "goal_rules": {"teleport_once": (240, 690), "run_away": True},
    })

    
    return levels


def mirror_level(level: dict) -> dict:
    import copy
    L = copy.deepcopy(level)
    world_w, world_h = L["world"]

    def mirror_rect(rect: pg.Rect) -> pg.Rect:
        return pg.Rect(world_w - rect.x - rect.w, rect.y, rect.w, rect.h)

    sx, sy = L["spawn"]
    L["spawn"] = (world_w - sx, sy)
    L["goal"] = mirror_rect(L["goal"])

    new_plats = []
    for item in L["platforms"]:
        kind = item[0]
        if kind in ("solid", "fake", "falling", "invisible"):
            _, rect = item
            new_plats.append((kind, mirror_rect(rect)))
        elif kind == "conveyor":
            _, payload = item
            rect, speed = payload[0], payload[1]
            boost = payload[2] if len(payload) >= 3 else 1.0
            new_plats.append(("conveyor", (mirror_rect(rect), -speed, boost)))
        elif kind == "moving":
            _, (rect, a, b, speed) = item
            rect2 = mirror_rect(rect)
            a2 = (world_w - a[0], a[1])
            b2 = (world_w - b[0], b[1])
            new_plats.append(("moving", (rect2, a2, b2, speed)))
        elif kind == "bounce":
            _, (rect, strength) = item
            new_plats.append(("bounce", (mirror_rect(rect), strength)))
        else:
            new_plats.append(item)

    L["platforms"] = new_plats
    L["spikes"] = [mirror_rect(s) for s in L.get("spikes", [])]
    L["control_zones"] = [mirror_rect(z) for z in L.get("control_zones", [])]

    new_tr = []
    for name, rect in L.get("triggers", []):
        new_tr.append((name, mirror_rect(rect) if rect else rect))
    L["triggers"] = new_tr

    new_ss = []
    for rect, vel in L.get("sliding_spikes", []):
        new_ss.append((mirror_rect(rect), (-vel[0], vel[1])))
    L["sliding_spikes"] = new_ss

    new_fs = []
    for rect, speed in L.get("falling_spikes", []):
        new_fs.append((mirror_rect(rect), speed))
    L["falling_spikes"] = new_fs

    new_rs = []
    for rect, speed in L.get("rising_spikes", []):
        new_rs.append((mirror_rect(rect), speed))
    L["rising_spikes"] = new_rs

    L["signs"] = [(mirror_rect(r), txt) for (r, txt) in L.get("signs", [])]

    gr = L.get("goal_rules", {})
    if "teleport_once" in gr:
        tx, ty = gr["teleport_once"]
        gr["teleport_once"] = (world_w - tx, ty)
    if "patrol" in gr:
        a, b, spd = gr["patrol"]
        gr["patrol"] = (world_w - a, world_w - b, spd)
    if "reset_to" in gr:
        tx, ty = gr["reset_to"]
        gr["reset_to"] = (world_w - tx, ty)
    L["goal_rules"] = gr

    return L
