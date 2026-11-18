import heapq
from typing import Dict, List, Tuple, Optional
from graph import Graph
from models import Zone


class PathFinder:
    """Find efficient paths through a graph using Dijkstra's algorithm."""

    def __init__(self, graph: Graph) -> None:
        """Initialize the pathfinder.

            Args:
                graph: Graph to search.
        """
        self.graph = graph

    def _zone_cost(self, zone: Zone) -> int:
        """Return the movement cost for entering a zone
            Args:
                zone: Zone being entered.

            Returns:
                Movement cost in turns.

            Raises:
                ValueError: If the zone is blocked
        """

        if zone.zone_type == "blocked":
            raise ValueError(
                f"Cannot enter blocked zone '{zone.name}'."
            )

        if zone.zone_type == "restricted":
            return 2

        return 1

    def _priority_cost(self, zone: Zone) -> int:
        """Return the tie-breaking cost for a zone.

            Priority zones are prefered when two paths have
            sane movement cost

            Args:
                zone: Zone being considered.

            Returns:
                Tie-breaking value
        """

        if zone.zone_type == "priority":
            return 0

        return 1

    def find_path(
            self,
            start: Zone,
            end: Zone
    ) -> List[Zone]:
        """Find the lowest-cost path between two zones

            Args:
                start: Starting zone.
                end: Destination zone.

            Returns:
                List of zones representing the path.

            Rasies:
                ValuError: if the zones are invalid or no path exists.
        """

        if start not in self.graph.zones:
            raise ValueError(
                f"start zone '{start.name}' is not in the ghraph"
            )

        if end not in self.graph.zones:
            raise ValueError(
                f"end zone '{end.name}' not in the graph"
            )

        if start.zone_type == "blocked":
            raise ValueError(
                f"start zone '{start.name}' is blocked"
            )

        if end.zone_type == "blocked":

            raise ValueError(
                f"end zone '{end.name}' is blocked"
            )

        distances: Dict[Zone, Tuple[float, float]] = {
            zone: (float("inf"), float("inf"))
            for zone in self.graph.zones
        }

        previous: Dict[Zone, Optional[Zone]] = {
            zone: None
            for zone in self.graph.zones
        }

        distances[start] = (0, 0)

        queue: List[Tuple[float, float, int, Zone]] = []

        counter = 0

        heapq.heappush(
            queue,
            (0, 0, counter, start)
        )

        while queue:
            current_cost, current_priority, _, current = (
                heapq.heappop(queue)
            )
            current_distance = (
                current_cost,
                current_priority
            )

            if current_distance != distances[current]:
                continue

            if current == end:
                break

            for neighbor in self.graph.get_neighbors(current):
                if neighbor.zone_type == "blocked":
                    continue

                movement_cost = self._zone_cost(neighbor)
                priority_cost = self._priority_cost(neighbor)

                new_distance = (
                    current_cost + movement_cost,
                    current_priority + priority_cost
                )

                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    previous[neighbor] = current

                    counter += 1

                    heapq.heappush(
                        queue,
                        (
                            new_distance[0],
                            new_distance[1],
                            counter,
                            neighbor
                        )
                    )

        if distances[end][0] == float("inf"):
            raise ValueError(
                f"No path exists from '{start.name}' to '{end.name}'"
            )

        return self._reconstruct_path(
            previous,
            start,
            end
        )

    def _reconstruct_path(
            self,
            previous: Dict[Zone, Optional[Zone]],
            start: Zone,
            end: Zone
    ) -> List[Zone]:
        """Reconstruct a path using the predecessor map

            Args:
                previous: Mapping of zones to their predecessors.
                start: Starting zone.
                end: Destination zone.

            Returns:
                Ordered path form start to end.

            Raises:
                "ValuError if the path cannot be reconstructed.
        """

        path: List[Zone] = []
        current: Optional[Zone] = end

        while current is not None:
            path.append(current)

            if current == start:
                break

            current = previous[current]

        path.reverse()

        if not path or path[0] != start:
            raise ValueError(
                f"No path exists from '{start.name}' to '{end.name}'."
            )

        return path

    def path_cost(self, path: List[Zone]) -> int:
        """Calculate the total movement cost of the path.

            Args:
                Ordered list of zones.

            Returns:
                A total novement cost in turns.

            Raises:
                ValuError: If the path contains a blocked zone.
        """

        total_cost = 0

        if len(path) < 2:
            return 0

        for zone in path[1:]:
            total_cost += self._zone_cost(zone)

        return total_cost
