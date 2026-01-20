# Trust Issues

A 2D troll-style platformer built with Python and Pygame, focused on misleading mechanics,
trap-based level design, and player expectation subversion.

---

## Quick Start Guide

### Prerequisites

1. Make sure you have the following installed:
   - Python 3.10 or higher ([Download Python](https://www.python.org/downloads/))
   - Git ([Download Git](https://git-scm.com/downloads)) — optional, but recommended

2. Verify Python installation:
   ```
   python --version
3. Clone the Repository
```
git clone https://github.com/MaximoMaturana/trust_issues_pygame.git 
cd trust-issues-pygame
```
4. Create and Activate Virtual Environment

Windows:
```
python -m venv .venv
.\.venv\Scripts\activate
```
macOS / Linux:
```
python3 -m venv .venv
source .venv/bin/activate
```

Once activated, you should see (.venv) at the start of your terminal line.

5. Install Dependencies

- This project only requires Pygame:
```
pip install pygame
```

- (Optional but recommended)
```
pip install --upgrade pip
```

6. Run the Game
```
python main.py
```

- The game window should open automatically.

## Controls

- Move Left / Right: A / D or Left / Right Arrow

- Jump: Space (also supports W / Up Arrow)

- Restart Level: R

- Return to Level Select: ESC

- Toggle Mirrored Mode (Level Select): M


## Troubleshooting

### Common Issues & Solutions

1. `ModuleNotFoundError: No module named 'pygame' `
```
pip install pygame
```

2. Game closes immediately

- Run the game from the terminal instead of double-clicking:
```
python main.py
```

3. Virtual environment not activating

- Make sure you are inside the project folder

- On Windows, ensure scripts are enabled:
```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
