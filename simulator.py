"""Turn-based simulation for routing drones through a graph."""

from typing import Dict, List, Set, Tuple, Optional
from graph import Graph
from models import Connection, Drone, Zone
from pathfinder import PathFinder


class Simulation:
    """Simulate drones moving through a graph under capacity constraints."""

    def __init__(self, graph: Graph, number_of_drones: int) -> None:
        """Initialize drones and calculate their routes.

        Args:
            graph: Connected zones used by the simulation.
            number_of_drones: Number of drones to route.

        Raises:
            ValueError: If the number of drones is not positive or no route
                exists between the start and end hubs.
        """
        if number_of_drones <= 0:
            raise ValueError("Number of drones must be positive.")

        self.graph = graph
        self.number_of_drones = number_of_drones
        self.pathfinder = PathFinder(graph)
        self.drones: List[Drone] = [
            Drone(index, graph.start_hub)
            for index in range(1, number_of_drones + 1)
        ]
        self.paths: Dict[int, List[Zone]] = {}
        self.path_indexes: Dict[int, int] = {}
        self.turn = 0
        self.history: List[List[str]] = []
        # self.capacity_history: List[Dict[str, Dict[str: int]]] = []
        self._calculate_paths()

    def _calculate_paths(self) -> None:
        """Find candidate routes and assign drones across them."""

        candidates = self._find_candidate_paths()
        if not candidates:
            raise ValueError(
                f"No path exists from {self.graph.start_hub.name} to "
                f"{self.graph.end_hub.name}."
            )

        path_loads = {index: 0 for index in range(len(candidates))}
        # this helps distribute drones across different routes
        for drone in self.drones:
            # The loop takes the first drone.
            # min() finds the best candidate path for that drone.
            best_index = min(
                range(len(candidates)),
                key=lambda index: (
                    self.pathfinder.path_cost(candidates[index])
                    + path_loads[index],
                    -sum(
                        zone.zone_type == "priority"
                        for zone in candidates[index]
                    ),
                    path_loads[index],
                    index,
                ),
            )
            # it assigns a path
            self.paths[drone.drone_id] = candidates[best_index]

            # initialize drone position at the beginning of its path
            self.path_indexes[drone.drone_id] = 0

            # updated the path_loads with number of drones
            path_loads[best_index] += 1

    def _find_candidate_paths(self) -> List[List[Zone]]:
        """Find alternative paths between start and end hubs.

            Returns: A list of candiate paths with connected zones,
                or and epty list if no path exists
        """
        try:
            first_path = self.pathfinder.find_path(
                self.graph.start_hub, self.graph.end_hub
            )
        except ValueError:
            return []

        candidates = [first_path]
        max_candidates = min(
            max(3, self.number_of_drones),
            len(self.graph.connections) + 1,
        )
        checked_edges: Set[Tuple[Zone, Zone]] = set()

        while len(candidates) < max_candidates:
            best_path: List[Zone] = []
            best_score: Tuple[int, int, int] | None = None

            for path in list(candidates):
                for index in range(len(path) - 1):
                    first, second = path[index], path[index + 1]
                    edge = (first, second)
                    reverse_edge = (second, first)
                    if edge in checked_edges or reverse_edge in checked_edges:
                        continue
                    checked_edges.add(edge)

                    alternative = self._find_path_without_edge(first, second)
                    if alternative is None or alternative in candidates:
                        continue

                    score = (
                        self.pathfinder.path_cost(alternative),
                        -sum(
                            zone.zone_type == "priority"
                            for zone in alternative
                        ),
                        self._count_shared_edges(alternative, candidates),
                    )
                    if best_score is None or score < best_score:
                        best_score = score
                        best_path = alternative

            if not best_path:
                break
            candidates.append(best_path)

        candidates.sort(
            key=lambda path: (
                self.pathfinder.path_cost(path),
                -sum(zone.zone_type == "priority" for zone in path),
                len(path),
            )
        )
        return candidates

    def _find_path_without_edge(
        self, blocked_zone1: Zone, blocked_zone2: Zone
    ) -> List[Zone] | None:
        """Find an alternative path without specified connection.

            Returns:
                An alternative path, or None if no path.
        """
        connections = [
            connection
            for connection in self.graph.connections
            if not connection.connects(blocked_zone1, blocked_zone2)
        ]
        temporary_graph = Graph(
            self.graph.zones,
            connections,
            self.graph.start_hub,
            self.graph.end_hub,
        )
        try:
            return PathFinder(temporary_graph).find_path(
                self.graph.start_hub, self.graph.end_hub
            )
        except ValueError:
            return None

    def _count_shared_edges(
        self, path: List[Zone], existing_paths: List[List[Zone]]
    ) -> int:
        """Count edges shared between a path and  existing paths.

            Returns:
                The number of shared edges.
        """
        shared = 0
        for first, second in zip(path, path[1:]):
            for existing in existing_paths:
                if any(
                    (first == a and second == b)
                    or (first == b and second == a)
                    for a, b in zip(existing, existing[1:])
                ):
                    shared += 1
                    break
        return shared

    def run(self) -> List[List[str]]:
        """Run until every drone reaches the end hub.

        Returns:
            Movement tokens grouped by simulation turn.

        Raises:
            RuntimeError: If the simulation deadlocks or exceeds its limit.
        """
        while not self._all_delivered():
            self.turn += 1
            if self.turn > self._maximum_turns():
                raise RuntimeError(
                    "Simulation could not finish within a safe turn limit."
                )

            movements = self._run_turn()
            # i add here 203, 204 lines
            # self.history.append(movements)
            # self.capacity_history.append(self.capacity_snapshot())
            if not movements and not self._all_delivered():
                raise RuntimeError(
                    "Simulation is deadlocked: no legal movement is possible."
                )
            self.history.append(movements)
        return self.history

    def _run_turn(self) -> List[str]:
        """Processes one simulatiion turn, drone movements and drone arrivals.

            Returns:
                A list of movements descriptions for the current turn.
        """
        movements: List[str] = []

        in_transit_at_start = {
            drone.drone_id for drone in self.drones if drone.is_in_transit()
        }
        arriving_ids = self._finish_transit(movements)

        # means set union: it combines the two sets.
        unavailable_ids = in_transit_at_start | arriving_ids

        occupied = self._occupied_zone_counts()
        link_usage = self._active_connection_counts()
        reserved_destinations = self._transit_destination_counts()

        candidates = self._movement_candidates(unavailable_ids)
        for _, drone_id, destination in candidates:
            drone = self._get_drone(drone_id)
            if drone.delivered or drone.is_in_transit():
                continue

            current = drone.current_zone
            connection = self.graph.get_connection(current, destination)

            if not self._zone_has_capacity(
                destination, occupied, reserved_destinations
            ):
                continue
            if link_usage.get(connection, 0) >= connection.max_link_capacity:
                continue

            occupied[current] = max(0, occupied.get(current, 0) - 1)
            link_usage[connection] = link_usage.get(connection, 0) + 1
            self.path_indexes[drone_id] += 1

            if destination.zone_type == "restricted":
                drone.transit_connection = connection
                drone.transit_destination = destination
                drone.transit_remaining = 1
                reserved_destinations[destination] = (
                    reserved_destinations.get(destination, 0) + 1
                )
                movements.append(
                    f"D{drone_id}-{connection.zone1.name}-"
                    f"{connection.zone2.name}"
                )
                continue

            drone.current_zone = destination
            if destination != self.graph.end_hub:
                occupied[destination] = occupied.get(destination, 0) + 1
            movements.append(f"D{drone_id}-{destination.name}")
            if destination == self.graph.end_hub:
                drone.delivered = True

        return movements

    def _finish_transit(self, movements: List[str]) -> Set[int]:
        """Complete tranist for drones that have reached their destinations.

            Args:
                movements: List of movement description to update.
            Returns:
                Set of Drone ID's that arrive during the same turn.
            Raises:
                RuntimeError: If a drone has no destination or a zone exceeds
                    its maximum capacity.
        """
        arriving: List[Tuple[Drone, Zone]] = []
        for drone in self.drones:
            if not drone.is_in_transit():
                continue
            drone.transit_remaining -= 1
            if drone.transit_remaining <= 0:
                destination = drone.transit_destination
                if destination is None:
                    raise RuntimeError(
                        f"Drone {drone.drone_id} transit has no destination."
                    )
                arriving.append((drone, destination))

        arriving_ids: Set[int] = set()
        for drone, destination in arriving:
            drone.current_zone = destination
            drone.transit_connection = None
            drone.transit_destination = None
            drone.transit_remaining = 0
            arriving_ids.add(drone.drone_id)
            movements.append(f"D{drone.drone_id}-{destination.name}")
            if destination == self.graph.end_hub:
                drone.delivered = True
        occupancy = self._occupied_zone_counts()
        for zone in self.graph.zones:
            if zone in (self.graph.start_hub, self.graph.end_hub):
                continue
            if occupancy.get(zone, 0) > zone.max_drones:
                raise RuntimeError(
                    f"Zone '{zone.name}' exceeded capacity during "
                    "transit arrival."
                )
        return arriving_ids

    def _movement_candidates(
        self, excluded_ids: Optional[Set[int]] = None
    ) -> List[Tuple[Tuple[int, int, int], int, Zone]]:

        """Generate and sort possible drone movements by priority.

            Args:
                excluded_ids: Drone IDs to exclude from movement candidates.

            Returns:
                Sorted List

        """
        excluded = excluded_ids or set()

        candidates: List[Tuple[Tuple[int, int, int], int, Zone]] = []

        for drone in self.drones:
            if drone.delivered or drone.is_in_transit():
                continue
            if drone.drone_id in excluded:
                continue

            path_index = self.path_indexes[drone.drone_id]
            path = self.paths[drone.drone_id]
            if path_index >= len(path) - 1:
                continue

            destination = path[path_index + 1]
            remaining_path = path[path_index:]
            score = (
                self.pathfinder.path_cost(remaining_path),
                -sum(
                    zone.zone_type == "priority"
                    for zone in remaining_path
                ),
                drone.drone_id,
            )
            candidates.append((score, drone.drone_id, destination))

        candidates.sort(key=lambda item: item[0])
        return candidates

    def _occupied_zone_counts(self) -> Dict[Zone, int]:

        """Count drones physically occupying zones right now.

            Returns:
                A dictionary with zone and number of drones occupying it.

        """
        counts = {zone: 0 for zone in self.graph.zones}
        for drone in self.drones:
            if not drone.delivered and not drone.is_in_transit():
                counts[drone.current_zone] += 1
        return counts

    def _transit_destination_counts(self) -> Dict[Zone, int]:
        """Count zone slots reserved by drones that are still in transit.

            Returns:
                A dictionary with zone and number of drones in tranist.
        """
        counts: Dict[Zone, int] = {}
        for drone in self.drones:
            if drone.is_in_transit() and drone.transit_destination is not None:
                destination = drone.transit_destination
                counts[destination] = counts.get(destination, 0) + 1
        return counts

    def _zone_has_capacity(
        self,
        destination: Zone,
        occupied_counts: Dict[Zone, int],
        reserved_destinations: Dict[Zone, int],
    ) -> bool:

        """Check capacity using occupancy plus transit reservations.

            Returns:
                bool: True if the destination has available capacity,
                False otherwise.

        """
        if destination in (self.graph.start_hub, self.graph.end_hub):
            return True
        occupied = occupied_counts.get(destination, 0)
        reserved = reserved_destinations.get(destination, 0)
        return occupied + reserved < destination.max_drones

    def _active_connection_counts(self) -> Dict[Connection, int]:
        """Count drones that remain on connections during transit.

            Returns:
                 A dictionary mapping each connection to the number of drones.

        """
        counts = {connection: 0 for connection in self.graph.connections}
        for drone in self.drones:
            if drone.is_in_transit() and drone.transit_connection is not None:
                counts[drone.transit_connection] += 1
        return counts

    def _get_drone(self, drone_id: int) -> Drone:
        """Return a drone.

             Returns:
                The drone with the specified ID.

            Raises:
                ValueError: If the drone ID is unknown.

        """
        for drone in self.drones:
            if drone.drone_id == drone_id:
                return drone
        raise ValueError(f"Unknown drone ID {drone_id}.")

    def _all_delivered(self) -> bool:
        """Return whether every drone has reached the end hub."""
        return all(drone.delivered for drone in self.drones)

    def _maximum_turns(self) -> int:
        """Return a generous guard against infinite simulations."""
        longest_cost = max(
            (self.pathfinder.path_cost(path) for path in self.paths.values()),
            default=1,
        )
        return longest_cost * max(self.number_of_drones, 1) * 10 + 100

    def capacity_snapshot(self) -> Dict[str, Dict[str, int]]:
        """Return used zone and connection capacity.

            Returns:
                A dictionary containing the used capacity
                of each zone and connection.

        """

        zones: Dict[str, int] = {}
        occupancy = self._occupied_zone_counts()
        transit_reservations = self._transit_destination_counts()

        for zone in self.graph.zones:
            if zone in (self.graph.start_hub, self.graph.end_hub):
                zones[zone.name] = 0
            else:
                zones[zone.name] = (
                    occupancy.get(zone, 0)
                    + transit_reservations.get(zone, 0)
                )

        links: Dict[str, int] = {}
        active = self._active_connection_counts()

        for connection in self.graph.connections:
            name = f"{connection.zone1.name}-{connection.zone2.name}"
            links[name] = active.get(connection, 0)

        return {"zones": zones, "links": links}
