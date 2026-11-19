*This project has been created as part of the 42 curriculum by agkicina.*

# Drone Routing Simulation

## Description

This project is a drone routing simulation that models how multiple drones travel through a network of connected hubs. The main goal is to move all drones from a starting hub to a destination hub while respecting the capacity limits of both hubs and connections.

Each hub can have a different type, which affects how drones can travel through the network:

- **Normal:** Standard hub that drones can pass through normally.
- **Restricted:** Requires an extra turn for drones to pass through.
- **Priority:** Preferred when multiple routes have the same movement cost.
- **Blocked:** Cannot be used by drones and is excluded from valid routes.

Connections between hubs are bidirectional and can have a maximum capacity, which determines how many drones can use the same connection at the same time.

The project focuses on route calculation, route distribution, and turn-based movement while handling different constraints. It also includes a visual interface that displays the map and drone movements in real time, making it easier to understand how the simulation works.

## Instructions

### Requirements

- Python 3
- `make`
- Dependencies listed in `requirements.txt`

### Installation

First, create a virtual environment and install the required dependencies:

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

You can also run the program directly by providing another map file as an argument:

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
| SPACE | Pause or resume the simulation. |
| RIGHT | Move forward to the next turn. |
| LEFT | Go back to the previous turn. |
| R | Restart the simulation. |
| ESC | Quit the application. |

## Algorithm and implementation

### Map representation

The map is represented as a graph structure:

- Hubs are represented as nodes.
- Connections between hubs are represented as edges.
- Each connection stores its maximum capacity.

The `MapParser` is responsible for reading the map file, creating the hubs and connections, and checking that the input data is valid. It also supports optional metadata, allowing additional properties such as hub types, colors, and capacities to be defined.

This representation makes it possible to work with different map configurations and apply routing algorithms to the network.

### Pathfinding

The project uses **Dijkstra's algorithm** to find routes from the starting hub to the destination.

Each hub has a movement cost that determines how much time a drone needs to pass through it:

- Normal hub: 1
- Priority hub: 1
- Restricted hub: 2
- Blocked hub: Cannot be used

When multiple routes have the same total movement cost, the algorithm gives preference to routes that pass through more priority hubs.

This allows the simulator to consider not only the shortest movement cost but also the characteristics of the hubs along each possible route.

### Route selection

The simulator first calculates an initial route using Dijkstra's algorithm. After that, it searches for alternative routes by temporarily removing connections from existing candidate paths and running the pathfinding algorithm again.

Once the available routes have been identified, each drone is assigned a route according to its path cost and the current load of that route. Priority hubs are also taken into consideration when comparing routes with equal scores.

This approach helps distribute drones across different available paths instead of sending all of them through a single route. It also helps make better use of the network while respecting its limitations.

### Simulation

Routes are calculated when the simulation starts. The simulator then manages the movement of drones turn by turn until they reach their destination.

Before each movement, several conditions are checked:

- Whether the destination hub has available capacity.
- Whether the connection has available capacity.
- Whether another drone has already reserved the destination hub or connection.
- Whether the drone has already completed its journey.

Restricted hubs add an extra turn of travel time, while blocked hubs are never included in valid routes.

The simulator also keeps track of reservations to prevent multiple drones from exceeding the available capacity during the same turn.

The simulation continues until all drones reach the destination or a deadlock or maximum-turn safety limit is detected. This ensures that the program can handle situations where movement becomes impossible or progress stops.

## Visual representation

The project uses **Pygame** to display the map and the simulation through a graphical interface.

The visual interface provides an overview of the network and allows users to follow the movement of each drone turn by turn.

It displays:

- Hubs, their names, and their positions.
- Connections between hubs and their capacity limits.
- Drones and their IDs.
- The starting and destination hubs.
- The current turn and the number of drones.
- A legend explaining the different hub types.

Different colors are used to distinguish the hub types:

- Blue: Normal
- Orange: Restricted
- Green: Priority
- Gray: Blocked
- Green: Start hub
- Red: Destination hub

The interface also allows users to pause and restart the simulation or move forward and backward between turns. This makes it easier to observe how drones share routes, interact with each other, and respect the capacity restrictions of the network.

## Example input

The project includes a sample file called `map.txt`. It contains the number of drones, several alternative routes, dead ends, loops, restricted hubs, priority hubs, and capacity limits.

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
- One starting hub.
- One destination hub.
- The hubs and their connections.

Optional metadata can also be used to define additional properties, such as hub types, colors, and connection capacities.

## Expected output

For the example above, the program performs the following steps:

1. Reads and validates the map file.
2. Builds the network of hubs and connections.
3. Finds a valid route from `start` to `goal`.
4. Assigns routes to the available drones.
5. Simulates their movements while respecting hub and connection capacities.
6. Displays the simulation in the Pygame window.
7. Prints the movement history for each turn and the total number of turns required.

The exact movement history and total number of turns depend on the map configuration and the routing and capacity decisions made during the simulation.

## Resources and AI usage

### Resources

The following resources were useful for understanding and implementing the main concepts used in this project:

- [Pygame documentation](https://www.pygame.org/docs/) — Official documentation used to understand the Pygame library, especially its graphical interface, event handling, and rendering features.
- [Dijkstra's algorithm](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm) — Reference for understanding shortest-path algorithms and their application to graph-based routing problems.
- [Python documentation](https://docs.python.org/3/) — Reference for Python syntax, standard libraries, and general programming concepts.

### AI usage

ChatGPT was used as a supporting tool during the development of this project, mainly to help review and better understand certain parts of the implementation.

In particular, AI assistance was used for the Pygame visualization part, especially rendering for understanding how graphical components are displayed and updated during the simulation.