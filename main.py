"""Main entry point for the drone simulation."""

import sys
import argparse
from parser import MapParser
from simulator import Simulation
from visualizer import DroneVisualizer


def main() -> int:
    """Run the drone simulation."""

    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("map_file")
    args = argument_parser.parse_args()
    map_file = args.map_file

    try:
        parser = MapParser()
        graph, drone_count = parser.parse(map_file)
        simulator = Simulation(graph, drone_count)
        history = simulator.run()
        visualizer = DroneVisualizer(graph, history, drone_count)
        visualizer.run()

    except (ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    for tur_number, movements in enumerate(history, start=1):
        print(f"Turn: {tur_number}: {' '.join(movements)}")

    print("Total Turns:", len(history))
    return 0


if __name__ == "__main__":
    sys.exit(main())
