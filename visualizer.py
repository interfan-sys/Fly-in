
"""Pygame visualization for the drone simulation."""

import re
from typing import Dict, List, Optional, Tuple
import pygame
from graph import Graph


WINDOW_WIDTH = 1800
WINDOW_HEIGHT = 800
MARGIN = 80
FPS = 60
TURN_DELAY = 700

BACKGROUND = (25, 29, 40)
TEXT_COLOR = (235, 239, 245)
EDGE_COLOR = (100, 111, 130)
DRONE_COLOR = (0, 255, 0)

ZONE_COLORS = {
    "normal": (90, 170, 220),
    "restricted": (225, 155, 65),
    "priority": (80, 200, 140),
    "blocked": (100, 105, 115),
}


class DroneVisualizer:
    """Display and animate drones moving through a graph."""

    def __init__(
        self,
        graph: Graph,
        history: List[List[str]],
        number_of_drones: Optional[int] = None
    ) -> None:
        """Initialize the visualization.

        Args:
            graph: The parsed map graph.
            history: Movement tokens grouped by simulation turn.
            number_of_drones: Number of drones in the simulation.
        """
        self.graph = graph
        self.history = history
        self.number_of_drones = (
            number_of_drones
            if number_of_drones is not None
            else self._infer_drone_count()
        )

        self.turn_index = 0
        self.paused = False
        self.running = True
        self.last_advance = 0

        self.drone_positions: Dict[int, str] = {
            drone_id: graph.start_hub.name
            for drone_id in range(1, self.number_of_drones + 1)
        }

        self.zone_positions: Dict[str, Tuple[int, int]] = {}
        self._initialize_pygame()
        self._calculate_positions()

    def _initialize_pygame(self) -> None:
        """Initialize the Pygame window and fonts."""
        pygame.init()
        pygame.display.set_caption("Drone Simulation")
        self.screen = pygame.display.set_mode(
            (WINDOW_WIDTH, WINDOW_HEIGHT)
        )
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 17)
        self.small_font = pygame.font.SysFont("arial", 13)
        self.title_font = pygame.font.SysFont("arial", 25, bold=True)

    def _infer_drone_count(self) -> int:
        """Infer the largest drone ID from movement history."""
        largest_id = 0

        for turn in self.history:
            for token in turn:
                match = re.match(r"^D(\d+)", token)
                if match:
                    largest_id = max(largest_id, int(match.group(1)))

        return largest_id

    def _calculate_positions(self) -> None:
        """Scale map coordinates to fit inside the window."""
        zones = self.graph.zones

        if not zones:
            return

        x_values = [zone.coordinates[0] for zone in zones]
        y_values = [zone.coordinates[1] for zone in zones]

        min_x, max_x = min(x_values), max(x_values)
        min_y, max_y = min(y_values), max(y_values)

        available_width = WINDOW_WIDTH - 2 * MARGIN
        available_height = WINDOW_HEIGHT - 2 * MARGIN - 100

        x_range = max(max_x - min_x, 1)
        y_range = max(max_y - min_y, 1)

        scale = min(
            available_width / x_range,
            available_height / y_range,
        )

        map_width = x_range * scale
        map_height = y_range * scale

        offset_x = (WINDOW_WIDTH - map_width) / 2
        offset_y = 45 + (available_height - map_height) / 2

        for zone in zones:
            x, y = zone.coordinates
            screen_x = int(offset_x + (x - min_x) * scale)
            screen_y = int(
                offset_y + available_height - (y - min_y) * scale
            )
            self.zone_positions[zone.name] = (screen_x, screen_y)

    def _zone_color(self, zone: object) -> Tuple[int, int, int]:
        """Return the display color for a zone."""
        zone_name = getattr(zone, "name")
        zone_type = getattr(zone, "zone_type", "normal")
        custom_color = getattr(zone, "color", None)

        if zone_name == self.graph.start_hub.name:
            return (100, 220, 130)

        if zone_name == self.graph.end_hub.name:
            return (245, 100, 115)

        if custom_color:
            try:
                color = pygame.Color(custom_color)
                return (color.r, color.g, color.b)
            except ValueError:
                pass

        return ZONE_COLORS.get(zone_type, ZONE_COLORS["normal"])

    def _draw_connections(self) -> None:
        """Draw graph connections and their capacities."""
        for connection in self.graph.connections:
            start = self.zone_positions.get(connection.zone1.name)
            end = self.zone_positions.get(connection.zone2.name)

            if start is None or end is None:
                continue

            pygame.draw.line(
                self.screen, EDGE_COLOR, start, end, 3
            )

            midpoint = (
                (start[0] + end[0]) // 2,
                (start[1] + end[1]) // 2,
            )

            capacity_text = self.small_font.render(
                str(connection.max_link_capacity),
                True,
                TEXT_COLOR,
            )
            self.screen.blit(
                capacity_text,
                (midpoint[0] + 4, midpoint[1] + 4),
            )

    def _draw_zones(self) -> None:
        """Draw zones, names, and occupancy limits."""
        for zone in self.graph.zones:
            position = self.zone_positions.get(zone.name)

            if position is None:
                continue

            color = self._zone_color(zone)
            radius = 22

            pygame.draw.circle(
                self.screen, color, position, radius
            )
            pygame.draw.circle(
                self.screen, TEXT_COLOR, position, radius, 2
            )

            name_surface = self.font.render(
                zone.name, True, TEXT_COLOR
            )
            name_rect = name_surface.get_rect(
                center=(position[0], position[1] - 35)
            )
            self.screen.blit(name_surface, name_rect)

            if zone.name == self.graph.start_hub.name:
                detail = "START"
            elif zone.name == self.graph.end_hub.name:
                detail = "GOAL"
            elif zone.zone_type == "blocked":
                detail = "BLOCKED"
            else:
                detail = f"Cap: {zone.max_drones}"

            detail_surface = self.small_font.render(
                detail, True, TEXT_COLOR
            )
            detail_rect = detail_surface.get_rect(
                center=(position[0], position[1] + 36)
            )
            self.screen.blit(detail_surface, detail_rect)

    def _apply_turn(self, turn_index: int) -> None:
        """Apply movement tokens for one turn.

        Expected token format: D1-zone_name.
        """
        if turn_index < 0 or turn_index >= len(self.history):
            return

        for token in self.history[turn_index]:
            match = re.match(r"^D(\d+)-(.+)$", token)

            if match is None:
                continue

            drone_id = int(match.group(1))
            destination = match.group(2)

            if destination in self.zone_positions:
                self.drone_positions[drone_id] = destination

    def _rebuild_positions(self, turn_index: int) -> None:
        """Reconstruct drone positions up to the requested turn."""
        self.drone_positions = {
            drone_id: self.graph.start_hub.name
            for drone_id in range(1, self.number_of_drones + 1)
        }

        for index in range(turn_index):
            self._apply_turn(index)

    def _draw_drones(self) -> None:
        """Draw drones at their current zones."""
        zone_counts: Dict[str, int] = {}

        for drone_id, zone_name in sorted(self.drone_positions.items()):
            position = self.zone_positions.get(zone_name)

            if position is None:
                continue

            offset = zone_counts.get(zone_name, 0)
            zone_counts[zone_name] = offset + 1

            # Spread drones in a small circle around their zone.
            angle = offset * 2.4
            dx = int(13 * pygame.math.Vector2(1, 0).rotate(
                angle * 180 / 3.14159
            ).x)
            dy = int(13 * pygame.math.Vector2(1, 0).rotate(
                angle * 180 / 3.14159
            ).y)

            drone_position = (
                position[0] + dx,
                position[1] + dy,
            )

            pygame.draw.circle(
                self.screen,
                DRONE_COLOR,
                drone_position,
                8,
            )

            label = self.small_font.render(
                str(drone_id), True, BACKGROUND
            )
            label_rect = label.get_rect(center=drone_position)
            self.screen.blit(label, label_rect)

    def _draw_interface(self) -> None:
        """Draw the title, status, and keyboard instructions."""
        title = self.title_font.render(
            "Drone Simulation", True, TEXT_COLOR
        )
        self.screen.blit(title, (20, 15))

        status = (
            f"Turn: {self.turn_index}/{len(self.history)}"
            f"    Drones: {self.number_of_drones}"
        )

        if self.paused:
            status += "    PAUSED"

        status_surface = self.font.render(
            status, True, TEXT_COLOR
        )
        self.screen.blit(status_surface, (20, WINDOW_HEIGHT - 55))

        instructions = (
            "SPACE: Pause/Resume   RIGHT: Next turn   "
            "LEFT: Previous turn   R: Restart   ESC: Quit"
        )
        instruction_surface = self.small_font.render(
            instructions, True, TEXT_COLOR
        )
        self.screen.blit(
            instruction_surface, (20, WINDOW_HEIGHT - 28)
        )

        legend_y = WINDOW_HEIGHT - 85
        legend_items = [
            ("Normal", ZONE_COLORS["normal"]),
            ("Restricted", ZONE_COLORS["restricted"]),
            ("Priority", ZONE_COLORS["priority"]),
            ("Blocked", ZONE_COLORS["blocked"]),
        ]

        x = 20
        for label, color in legend_items:
            pygame.draw.circle(
                self.screen, color, (x + 6, legend_y + 7), 6
            )
            text_surface = self.small_font.render(
                label, True, TEXT_COLOR
            )
            self.screen.blit(text_surface, (x + 17, legend_y))
            x += 120

    def _advance_turn(self) -> None:
        """Advance the animation by one turn."""
        if self.turn_index >= len(self.history):
            return

        self._apply_turn(self.turn_index)
        self.turn_index += 1

    def run(self) -> None:
        """Run the Pygame event and animation loop."""
        try:
            while self.running:
                current_time = pygame.time.get_ticks()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False

                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False

                        elif event.key == pygame.K_SPACE:
                            self.paused = not self.paused

                        elif event.key == pygame.K_RIGHT:
                            self._advance_turn()

                        elif event.key == pygame.K_LEFT:
                            self.turn_index = max(
                                0, self.turn_index - 1
                            )
                            self._rebuild_positions(self.turn_index)

                        elif event.key == pygame.K_r:
                            self.turn_index = 0
                            self.paused = False
                            self._rebuild_positions(0)

                if (
                    not self.paused
                    and self.turn_index < len(self.history)
                    and current_time - self.last_advance >= TURN_DELAY
                ):
                    self._advance_turn()
                    self.last_advance = current_time

                self.screen.fill(BACKGROUND)
                self._draw_connections()
                self._draw_zones()
                self._draw_drones()
                self._draw_interface()

                pygame.display.flip()
                self.clock.tick(FPS)

        finally:
            pygame.quit()
