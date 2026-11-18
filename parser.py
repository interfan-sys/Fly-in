from typing import Set, Tuple, Optional, Dict, List, cast
from models import Zone, Connection
from graph import Graph


class MapParser:
    """Parse Fly-in map files."""

    VALID_ZONE_TYPES: Set[str] = {
        "normal",
        "blocked",
        "restricted",
        "priority",
    }

    def parse(self, filename: str) -> Tuple[Graph, int]:

        """Parse a map file into a graph.

            Args:
                filename: Name of the imput file.

            Returns:
                A tuple containing the graph and drone count.

            Raises:
                ValuError: If the input file contains invalid data
                    or is missing required information.
        """

        drones: Optional[int] = None
        zones: Dict[str, Zone] = {}
        connections: List[Connection] = []
        connection_keys: Set[Tuple[str, str]] = set()
        start_hub: Optional[Zone] = None
        end_hub: Optional[Zone] = None

        with open(filename, "r", encoding="utf-8") as file:
            for line_number, raw_line in enumerate(file, 1):
                line = raw_line.strip()

                if not line or line.startswith("#"):
                    continue

                try:
                    line = line.replace("[", "").replace("]", "")
                    parts = line.split()
                    item_type = parts[0]
                    if item_type == "nb_drones:":
                        if drones is not None:
                            raise ValueError(
                                "Duplicate nb_drones declaration"
                            )

                        if len(parts) != 2:
                            raise ValueError(
                                "nb_drones requires one value"
                            )
                        drones = int(parts[1])
                        if drones <= 0:
                            raise ValueError(
                                "number of drones must be positive"
                            )

                    elif item_type in ("start_hub:", "end_hub:", "hub:"):
                        zone = self._parse_zone(parts, item_type)

                        if item_type == "start_hub:" and start_hub is not None:
                            raise ValueError(
                                "Duplicate start_hub"
                            )

                        if item_type == "end_hub:" and end_hub is not None:
                            raise ValueError(
                                "Duplicate end_hub"
                            )

                        if zone.name in zones:
                            raise ValueError(
                                f"Duplicate zone: '{zone.name}'"
                            )

                        zones[zone.name] = zone

                        if item_type == "start_hub:":
                            start_hub = zone
                        elif item_type == "end_hub:":
                            end_hub = zone

                    elif item_type == "connection:":
                        if len(parts) < 2:
                            raise ValueError(
                                "Connection requires zone1-zone2 pair"
                            )

                        names = parts[1].split("-")
                        if len(names) != 2:
                            raise ValueError(
                                "Connections must have the form "
                                "zone1-zone2"
                            )

                        zone1_name, zone2_name = names

                        if zone1_name == zone2_name:
                            raise ValueError(
                                "A connection can't connect a zone to itself"
                            )

                        if zone1_name not in zones:
                            raise ValueError(
                                f"Unknown '{zone1_name}'"
                            )

                        if zone2_name not in zones:
                            raise ValueError(
                                f"Unknown '{zone2_name}'"
                            )

                        key: Tuple[str, str] = cast(
                            Tuple[str, str],
                            tuple(sorted((zone1_name, zone2_name)))
                        )
                        if key in connection_keys:
                            raise ValueError(
                                "Duplicate connection"
                            )
                        metadata = self._parse_metadata(parts[2:])

                        capacity = self._positive_int(
                            metadata.get(
                                "max_link_capacity",
                                "1"), "max_link_capacity"
                            )

                        connection = Connection(
                            zones[zone1_name],
                            zones[zone2_name],
                            capacity
                        )

                        connections.append(connection)
                        connection_keys.add(key)

                    else:
                        raise ValueError(
                            f"Unknown declaration '{item_type}'"
                        )

                except ValueError as error:
                    raise ValueError(
                        f"Line {line_number}, {error}"
                    ) from error

        if drones is None:
            raise ValueError(
                "Map is missing nb_drones"
            )

        if start_hub is None:
            raise ValueError(
                "Map is missing start_hub"
            )

        if end_hub is None:
            raise ValueError(
                "Map is missing end_hub"
            )

        graph = Graph(
            list(zones.values()),
            connections,
            start_hub,
            end_hub
        )

        return graph, drones

    def _parse_zone(
            self,
            parts: List[str],
            item_type: str
            ) -> Zone:
        """Parse zone data from the input file into a Zone object.

            Args:
                parts: A list of strings containing zone information.
                item_type: The zone type check if "start_zone", "end_zone",
                    or "hub" in order to check for capacity max_drones.

            Returns:
                A zone object containing zone name, coordinates,
                    zone type, color and max number of drones.

            Raises:
                ValueError: If the zone definition is invalid or
                incomplete,
        """

        if len(parts) < 4:
            raise ValueError(
                "hub requires name, x and y coordinates"
            )
        name = parts[1]

        if "-" in name or " " in name:
            raise ValueError(
                "zone name cannot contain '-' or spaces"
            )
        try:
            x = int(parts[2])
            y = int(parts[3])
        except ValueError:
            raise ValueError(
                "coordinates must be integers"
            )

        metadata = self._parse_metadata(parts[4:])
        zone_type = metadata.get("zone", "normal")

        if zone_type not in self.VALID_ZONE_TYPES:
            raise ValueError(
                f"Invalid zone type '{zone_type}'"
            )

        color = metadata.get("color")

        if item_type in ("start_hub:", "end_hub:"):
            max_drones = 1

        else:
            max_drones = self._positive_int(
                metadata.get("max_drones", "1"),
                "max_drones"
            )

        return Zone(
            name,
            (x, y),
            zone_type,
            color,
            max_drones
        )

    def _parse_metadata(
            self,
            parts: List[str]
    ) -> Dict[str, str]:
        """Parse key=value metadata from a list of strings.

            Args:
                parts: A list of strings in key=value format.

            Returns:
                A dictionary containing metadata keys and values.

            Raises:
                ValueError: If metadeta item does not contain "=",
                    has an empty key or value or contains a duplicate key.
        """
        metadata: Dict[str, str] = {}

        for item in parts:
            if "=" not in item:
                raise ValueError(
                    f"Invalid metadata '{item}'"
                )

            key, value = item.split("=", 1)

            if not key or not value:
                raise ValueError(
                    f"Invalid metadata '{item}'"
                )
            if key in metadata:
                raise ValueError(
                    f"Duplicate metadata '{key}'"
                )

            metadata[key] = value

        return metadata

    def _positive_int(
            self,
            value: str,
            field_name: str
    ) -> int:
        """Convert a string to positive integer.

        Args:
            value: String to be converted.
            field_name: Name of the field being validated.

        Returns:
                The converted positive integer.

        Raises:
            ValueError: If the value is not an integer or is not positive.
        """
        try:
            number = int(value)
        except ValueError:
            raise ValueError(
                f"'{field_name}' must be an integer"
            )

        if number <= 0:
            raise ValueError(
                f"'{field_name}' must be positive integer"
            )

        return number
