*This project has been created as part of the 42 curriculum by agkicina.*

# Drone Routing Simulation

## Description

This project simulates drones travelling through a network of connected hubs. The goal is to move all drones from the start hub to the destination while respecting the capacity limits of hubs and connections.

Each hub can have a different type:

- Normal: Standard hub.
- Restricted: Takes an extra turn to pass through.
- Priority: Preferred when routes have the same movement cost.
- Blocked: Cannot be used.

Connections are bidirectional and can have a maximum capacity, which limits how many drones can use them at the same time.

The project also includes a visual interface that displays the map and drone movements turn by turn.

## Instructions

### Requirements

- Python 3
- `make`
- Dependencies listed in `requirements.txt`

### Installation

Create a virtual environment and install the dependencies:

```bash
make install
```

Activate the virtual environment:

```bash
source .venv/bin/activate
```

### Running the project

Run the simulation using the default `map.txt` file:

```bash
make run
```

You can also run the program directly with another map file:

```bash
python3 main.py path/to/map.txt
```

### Other Makefile commands

| Command | Description |
|---|---|
| `make install` | Creates a virtual environment and installs dependencies. |
| `make run` | Runs the simulation with `map.txt`. |
| `make debug` | Runs the program using Python's debugger. |
| `make lint` | Checks code style with Flake8 and types with Mypy. |
| `make clean` | Removes Python cache files and cache directories. |

### Visual controls

| Key | Action |
|---|---|
| SPACE | Pause or resume |
| RIGHT | Next turn |
| LEFT | Previous turn |
| R | Restart simulation |
| ESC | Quit |

## Algorithm and implementation

### Map representation

The map is represented as a graph:

- Hubs are the nodes.
- Connections are the edges.
- Each connection stores its maximum capacity.

The `MapParser` reads the map file, creates the hubs and connections, and checks that the input is valid. It also supports optional metadata such as hub types, colors, and capacities.

### Pathfinding

The project uses **Dijkstra's algorithm** to find routes from the start hub to the destination.

Each hub has a movement cost:

- Normal hub: 1
- Priority hub: 1
- Restricted hub: 2
- Blocked hub: Cannot be used

When two routes have the same movement cost, routes passing through more priority hubs are preferred.

### Route selection

The simulator first finds a route using Dijkstra's algorithm. It then searches for alternative routes by temporarily removing connections from existing candidate paths and running the pathfinder again.

Each drone is assigned a route based on its path cost and the current load of that route. Priority hubs are also considered when choosing between routes with equal scores.

This approach helps distribute drones across different possible paths.

### Simulation

Routes are calculated when the simulation starts. The simulator then moves the drones turn by turn.

Before each movement, it checks:

- Whether the destination hub has available capacity.
- Whether the connection has available capacity.
- Whether another drone has already reserved the destination or connection.
- Whether the drone has completed its journey.

Restricted hubs add an extra turn of travel time. Blocked hubs are never included in valid routes.

The simulation continues until all drones reach the destination or a deadlock or maximum-turn safety limit is detected.

## Visual representation

The project uses **Pygame** to display the map and the simulation.

The visual interface shows:

- Hubs, their names, and their positions.
- Connections and their capacity limits.
- Drones and their IDs.
- The start and destination hubs.
- The current turn and number of drones.
- A legend explaining the different hub types.

Different colors help distinguish the hub types:

- Blue: Normal
- Orange: Restricted
- Green: Priority
- Gray: Blocked
- Green: Start hub
- Red: Destination hub

The interface also allows the user to pause, restart, and move between turns. This makes it easier to follow the simulation and understand how drones share routes and respect capacity limits.

## Example input

The project includes a sample file called `map.txt`. It contains nb of drones, several alternative routes, dead ends, loops, restricted hubs, priority hubs, and capacity limits.

A smaller example of the map format:

```text
nb_drones: 2

start_hub: start 0 0
hub: middle 1 0
hub: priority_path 2 0 [zone=priority]
end_hub: goal 3 0

connection: start-middle
connection: middle-priority_path
connection: priority_path-goal
```

Each map file must define:

- The number of drones.
- One start hub.
- One destination hub.
- The hubs and their connections.

Optional metadata can define hub types, colors, and capacities.

## Expected output

For the example above, the program:

1. Reads and validates the map.
2. Finds a route from `start` to `goal`.
3. Assigns routes to the drones.
4. Simulates their movements while respecting capacities.
5. Displays the simulation in the Pygame window.
6. Prints the movement history for each turn and the total number of turns.

The exact movement history and number of turns depend on the map and the simulation's routing and capacity decisions.

## Resources and AI usage

### Resources

- [Pygame documentation](https://www.pygame.org/docs/)
- [Dijkstra's algorithm](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)

### AI usage

ChatGPT was used to help review and explain the visualisation part from pygame module particulary with rendering.