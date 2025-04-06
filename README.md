# IART - 24/25 - FEUP - Assignment_1 - Group A1_64

### Project Description

For our first assignment, we implemented a Python version of Baker´s Dozen Solitaire with both human-playable and AI-solving modes. The game features multiple AI algorithms including DFS, A*, Weighted A* and Greedy search to solve the solitaire game.

### Requirements
- Python 3.6 or higher;
- `pygame` library;
- A `png/` folder containing all card images (included in the project).

### Installation & Setup
- Unzip the project folder;
- Install the required dependencies, if not installed;
- Make sure the `png/` folder with all card images is in the same directory as the Python files (it should be by default).


### How to Run
- To start the game, run: `python3 main.py`.

### Game Modes

#### Human Mode

Play the game manually using the mouse.

**Features:**
- Click-and-drag controls;
- Undo Moves (up to 3 per game);
- Hint system (using AI);
- Time limit and scoring system.

#### AI Mode

Watch different AI algorithms attempt to solve the game.

**Available Algorithms:**
- Simple (rule-based);
- Random;
- Depth-First Search (DFS);
- DFS Improved (optimized);
- Iterative Deepening;
- Greedy Search;
- A* Search;
- Weighted A* Search.

**Extra functionality:** 
- The game can **read an initial game state** from a text file;
- After solving, the **solution is saved** to a `.txt` file.

### Controls
- **Mouse:** Click and drag cards to move;
- **Double-Click:** Auto-move to foundation when possible;
- **Buttons:** USe the menu to select game modes and options.

### Customization

You can tweak the gameplay and AI behavior:
- Change difficulty (ex: number of cards per suit: 4-13);
- Set time limits for both human and AI modes;
- Adjust AI settings:
    - Depth limits;
    - Maximum number of useless moves;
    - Heurisitc weights.

### File Structure
- `main.py`: Main game launcher;
- `game.py`: Game logic;
- `constants.py`: Game settings and constants;
- `class_solitaire_state.py`: Game state structure;
- `dfs_solver.py`: DFS-based solvers;
- `astar_solver.py`: A* solver;
- `weighted_astar_solver.py`: Weighted A* solver;
- `greedy.py`: Greedy solver;
- `iterative_deepening_solver.py`: Iterative Deepening solver;
- `tests.py`: File containing performance measurements for AI algorithms;
- `helpers.py`: Utility functions;
- `png/`: Folder with all card images;
- `initial.txt`: Text file containing an initial game state.

### Troubleshooting

If you run into issues:
- Confirm that all `png/` card images are in the `png/` folder;
- Make sure you are using a compatible Python version (3.6+);
- Ensure that `pygame` is correctly installed.

### Group Members

- Hugo Alexandre Almeida Barbosa - up202205774@edu.fe.up.pt
- João António Morgado Parada - up201405280@edu.fe.up.pt
- Luís Henrique da Cunha Castanho Gonçalves Ganço - up202004196@edu.fc.up.pt

