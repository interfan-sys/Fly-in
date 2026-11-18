from typing import List, Dict
from models import Zone, Connection


class Graph:
    """Represents a graph of zones and connections."""

    def __init__(
            self,
            zones: List[Zone],
            connections: List[Connection],
            start_hub: Zone,
            end_hub: Zone
    ) -> None:
        """Initialize the graph.

        Args:
            zones: All zones in the graph.
            connections: All connections between zones.
            start_hub: Starting zone.
            end_hub: Destination zone "Goal".
        """
        self.zones = zones
        self.connections = connections
        self.start_hub = start_hub
        self.end_hub = end_hub
        self.neighbors: Dict[Zone, List[Zone]] = {}
        self._build_neighbors()

    def _build_neighbors(self) -> None:
        """ Build the bidirectional neighbors list."""
        for zone in self.zones:
            self.neighbors[zone] = []

        for connection in self.connections:
            self.neighbors[connection.zone1].append(connection.zone2)
            self.neighbors[connection.zone2].append(connection.zone1)

    def get_neighbors(self, zone: Zone) -> List[Zone]:
        """Return zones directly connected to the given zone.

        Args:
            zone: Zone for which to find neighbors.

        Returns:
            A list of directly connected zones.
        """
        return self.neighbors.get(zone, [])

    def get_connection(
            self,
            zone1: Zone,
            zone2: Zone
    ) -> Connection:
        """Return a connection between zones.

            Args:
                zone1: First zone.
                zone2: Second zone.

            Returns:
                The connection between the two zones.

            Raises:
                ValueError: if no connection exists betwwen the zones.
        """
        for connection in self.connections:
            if connection.connects(zone1, zone2):
                return connection

        raise ValueError(
            f"No connection exists between "
            f"{zone1.name} and {zone2.name}"
        )
