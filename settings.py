# settings.py

# Game dimensions and title
WIDTH, HEIGHT = 1000, 600
FPS = 60
TITLE = "Trust Issues - A Not-So-Friendly Platformer"

# Physics settings
GRAVITY = 2200.0  # Gravity affecting the player
PLAYER_SPEED = 360.0  # Speed of the player
PLAYER_JUMP = 780.0  # Jump force
FRICTION = 0.82  # Friction applied to the player

# Quality of life settings for platforming
COYOTE_TIME = 0.10  # Jump allowed shortly after leaving a platform
JUMP_BUFFER = 0.10  # Jump pressed shortly before landing still counts

# Color definitions
BG = (15, 16, 22)  # Background color
WHITE = (245, 245, 245)  # White color
ACCENT = (255, 208, 90)  # Accent color
RED = (255, 80, 90)
GREEN = (110, 255, 170)
CYAN = (80, 220, 255)
PURPLE = (190, 120, 255)
DARK = (30, 32, 45)
