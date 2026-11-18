from typing import Optional, Tuple


class Zone:
    """Represent a zone in the drone graph."""

    def __init__(
            self,
            name: str,
            coordinates: Tuple[int, int],
            zone_type: str = "normal",
            color: Optional[str] = None,
            max_drones: int = 1
    ) -> None:
        """Initialize a zone.

        Args:
            name: Unique name of the zone.
            coordinates: X and Y coordinates.
            zone_type: Zone type.
            color: Optional display color.
            max_drones: Maximum number of drones in the zone.
        """
        self.name = name
        self.coordinates = coordinates
        self.zone_type = zone_type
        self.color = color
        self.max_drones = max_drones


class Connection:
    """Represent a bidirectional connection between two zones."""

    def __init__(
            self,
            zone1: Zone,
            zone2: Zone,
            max_link_capacity: int = 1
    ) -> None:
        """Initialize a connection.

        Args:
            zone1: First connected zone.
            zone2: Second connected zone.
            max_link_capacity: Maximum number of drones that can
                pass through the connection at the same time.
        """
        self.zone1 = zone1
        self.zone2 = zone2
        self.max_link_capacity = max_link_capacity

    def connects(self, first_zone: Zone, second_zone: Zone) -> bool:
        """Return whether this connection joins the two zones."""
        return (
            self.zone1 == first_zone and self.zone2 == second_zone
        ) or (
            self.zone1 == second_zone and self.zone2 == first_zone
        )


class Drone:
    """Represent a drone moving through the graph."""

    def __init__(self, drone_id: int, current_zone: Zone) -> None:
        """Initialize a drone.

        Args:
            drone_id: Unique identifier for the drone.
            current_zone: The Drone's current zone.
        """
        self.drone_id = drone_id
        self.current_zone = current_zone
        self.delivered: bool = False
        self.transit_connection: Optional[Connection] = None
        self.transit_destination: Optional[Zone] = None
        self.transit_remaining = 0

    def is_in_transit(self) -> bool:
        """Return whether the drone is currently travelling."""
        return self.transit_remaining > 0
