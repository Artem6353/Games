"""
Asteroids Game - Production Ready Implementation
================================================
A high-performance, object-pooled, spatially-hashed Asteroids game
with combo mechanics, meta-progression, and particle effects.

Author: Senior Game Developer
Architecture: ECS-inspired OOP with strict typing
"""

import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, Type, TypeVar, Generic

import pygame
from pygame.math import Vector2

# =============================================================================
# CONSTANTS AND CONFIGURATION
# =============================================================================

SCREEN_WIDTH: int = 1280
SCREEN_HEIGHT: int = 720
FPS: int = 60

# Colors (Neon style)
COLOR_BLACK: Tuple[int, int, int] = (5, 5, 10)
COLOR_WHITE: Tuple[int, int, int] = (255, 255, 255)
COLOR_CYAN: Tuple[int, int, int] = (0, 255, 255)
COLOR_ORANGE: Tuple[int, int, int] = (255, 165, 0)
COLOR_RED: Tuple[int, int, int] = (255, 50, 50)
COLOR_GREEN: Tuple[int, int, int] = (50, 255, 50)
COLOR_YELLOW: Tuple[int, int, int] = (255, 255, 0)
COLOR_PURPLE: Tuple[int, int, int] = (180, 50, 255)

# Ship constants
SHIP_SIZE: float = 20.0
SHIP_THRUST: float = 400.0
SHIP_MAX_SPEED: float = 400.0
SHIP_FRICTION: float = 0.98
SHIP_ROTATION_SPEED: float = 300.0

# Bullet constants
BULLET_SPEED: float = 600.0
BULLET_LIFETIME: float = 2.0
BULLET_RADIUS: float = 3.0

# Asteroid constants
ASTEROID_LARGE_RADIUS: float = 60.0
ASTEROID_MEDIUM_RADIUS: float = 35.0
ASTEROID_SMALL_RADIUS: float = 18.0
ASTEROID_LARGE_HP: int = 3
ASTEROID_MEDIUM_HP: int = 2
ASTEROID_SMALL_HP: int = 1

# Particle constants
PARTICLE_LIFETIME: float = 1.0
PARTICLE_FADE_RATE: float = 1.0

# Combo system
COMBO_DECAY_TIME: float = 3.0
COMBO_MULTIPLIER_STEP: float = 0.1
MAX_COMBO_MULTIPLIER: float = 5.0

# Shop upgrades
UPGRADE_COSTS = {
    'max_speed': [100, 200, 400, 800, 1600],
    'fire_rate': [150, 300, 600, 1200, 2400],
    'damage': [200, 400, 800, 1600, 3200],
    'magnet_radius': [50, 100, 200, 400, 800],
}

# Spatial grid
GRID_CELL_SIZE: int = 100

# =============================================================================
# OBJECT POOLING SYSTEM
# =============================================================================


T = TypeVar('T')


class Poolable(ABC):
    """Abstract base class for poolable objects."""
    
    def __init__(self) -> None:
        self.active: bool = False
        self.position: Vector2 = Vector2(0, 0)
        self.velocity: Vector2 = Vector2(0, 0)
        self.radius: float = 1.0
    
    @abstractmethod
    def reset(self) -> None:
        """Reset object to initial state for reuse."""
        pass
    
    @abstractmethod
    def update(self, dt: float) -> None:
        """Update object state."""
        pass
    
    @abstractmethod
    def render(self, surface: pygame.Surface, camera_offset: Vector2) -> None:
        """Render object to surface."""
        pass


class ObjectPool(Generic[T]):
    """
    Generic object pool for memory-efficient object reuse.
    Prevents garbage collection spikes during gameplay.
    """
    
    def __init__(self, object_class: Type[T], initial_size: int = 100, expandable: bool = True):
        self.object_class: Type[T] = object_class
        self.expandable: bool = expandable
        self._available: List[T] = []
        self._active: List[T] = []
        
        # Pre-allocate objects
        for _ in range(initial_size):
            obj = object_class()
            self._available.append(obj)
    
    def acquire(self) -> Optional[T]:
        """Acquire an object from the pool."""
        if self._available:
            obj = self._available.pop()
            obj.active = True
            self._active.append(obj)
            return obj
        
        if self.expandable:
            obj = self.object_class()
            obj.active = True
            self._active.append(obj)
            return obj
        
        return None
    
    def release(self, obj: T) -> None:
        """Return an object to the pool."""
        if obj in self._active:
            self._active.remove(obj)
            obj.reset()
            obj.active = False
            self._available.append(obj)
    
    def release_all(self) -> None:
        """Release all active objects."""
        for obj in list(self._active):
            self.release(obj)
    
    def get_active(self) -> List[T]:
        """Get list of active objects."""
        return self._active
    
    def update_all(self, dt: float) -> None:
        """Update all active objects."""
        for obj in self._active:
            obj.update(dt)
    
    def render_all(self, surface: pygame.Surface, camera_offset: Vector2) -> None:
        """Render all active objects."""
        for obj in self._active:
            obj.render(surface, camera_offset)
    
    @property
    def active_count(self) -> int:
        return len(self._active)
    
    @property
    def available_count(self) -> int:
        return len(self._available)


# =============================================================================
# SPATIAL HASH GRID FOR COLLISION DETECTION
# =============================================================================


class SpatialGrid:
    """
    Spatial hashing grid for O(1) average-case collision detection.
    Divides space into cells and only checks collisions between objects in same/adjacent cells.
    """
    
    def __init__(self, cell_size: int = GRID_CELL_SIZE):
        self.cell_size: int = cell_size
        self.grid: Dict[Tuple[int, int], Set[int]] = {}
        self.object_positions: Dict[int, Tuple[int, int]] = {}
    
    def clear(self) -> None:
        """Clear the spatial grid."""
        self.grid.clear()
        self.object_positions.clear()
    
    def _get_cell(self, position: Vector2) -> Tuple[int, int]:
        """Get grid cell coordinates for a position."""
        return (int(position.x // self.cell_size), int(position.y // self.cell_size))
    
    def insert(self, obj_id: int, position: Vector2) -> None:
        """Insert an object into the grid."""
        cell = self._get_cell(position)
        
        if cell not in self.grid:
            self.grid[cell] = set()
        
        self.grid[cell].add(obj_id)
        self.object_positions[obj_id] = cell
    
    def remove(self, obj_id: int) -> None:
        """Remove an object from the grid."""
        if obj_id in self.object_positions:
            cell = self.object_positions[obj_id]
            if cell in self.grid:
                self.grid[cell].discard(obj_id)
            del self.object_positions[obj_id]
    
    def update(self, obj_id: int, old_pos: Vector2, new_pos: Vector2) -> None:
        """Update object position in grid."""
        old_cell = self._get_cell(old_pos)
        new_cell = self._get_cell(new_pos)
        
        if old_cell != new_cell:
            self.remove(obj_id)
            self.insert(obj_id, new_pos)
    
    def get_nearby(self, position: Vector2, radius: float) -> Set[int]:
        """Get all object IDs in cells near the given position."""
        center_cell = self._get_cell(position)
        nearby_ids: Set[int] = set()
        
        # Check center cell and all 8 neighbors
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                cell = (center_cell[0] + dx, center_cell[1] + dy)
                if cell in self.grid:
                    nearby_ids.update(self.grid[cell])
        
        return nearby_ids
    
    def get_potential_collisions(self, objects: List['GameObject']) -> List[Tuple['GameObject', 'GameObject']]:
        """Get pairs of objects that might collide."""
        potential_pairs: List[Tuple['GameObject', 'GameObject']] = []
        checked_pairs: Set[Tuple[int, int]] = set()
        
        for obj in objects:
            if not obj.active:
                continue
            
            nearby_ids = self.get_nearby(obj.position, obj.radius * 2)
            
            for other_id in nearby_ids:
                if other_id == id(obj):
                    continue
                
                pair = tuple(sorted([id(obj), other_id]))
                if pair in checked_pairs:
                    continue
                
                checked_pairs.add(pair)
                
                # Find the other object
                for other_obj in objects:
                    if id(other_obj) == other_id and other_obj.active:
                        potential_pairs.append((obj, other_obj))
                        break
        
        return potential_pairs


# =============================================================================
# GAME ENTITIES
# =============================================================================


class GameObject(Poolable):
    """Base class for all game objects with unique ID tracking."""
    
    _id_counter: int = 0
    
    def __init__(self) -> None:
        super().__init__()
        GameObject._id_counter += 1
        self.id: int = GameObject._id_counter
        self.rotation: float = 0.0
        self.angular_velocity: float = 0.0
        self.damage_multiplier: float = 1.0
    
    def reset(self) -> None:
        """Reset to default state."""
        super().reset()
        self.position = Vector2(0, 0)
        self.velocity = Vector2(0, 0)
        self.rotation = 0.0
        self.angular_velocity = 0.0
        self.damage_multiplier = 1.0
    
    def wrap_position(self) -> None:
        """Wrap position around screen edges (toroidal space)."""
        if self.position.x < -self.radius:
            self.position.x = SCREEN_WIDTH + self.radius
        elif self.position.x > SCREEN_WIDTH + self.radius:
            self.position.x = -self.radius
        
        if self.position.y < -self.radius:
            self.position.y = SCREEN_HEIGHT + self.radius
        elif self.position.y > SCREEN_HEIGHT + self.radius:
            self.position.y = -self.radius
    
    def apply_friction(self, friction: float, dt: float) -> None:
        """Apply friction/drag to velocity."""
        self.velocity *= friction
    
    def move(self, dt: float) -> None:
        """Move object based on velocity."""
        self.position += self.velocity * dt
        self.rotation += self.angular_velocity * dt


class Ship(GameObject):
    """Player-controlled spaceship with inertia-based movement."""
    
    def __init__(self) -> None:
        super().__init__()
        self.max_speed: float = SHIP_MAX_SPEED
        self.thrust_power: float = SHIP_THRUST
        self.fire_cooldown: float = 0.0
        self.fire_rate: float = 0.15  # seconds between shots
        self.damage: float = 1.0
        self.magnet_radius: float = 150.0
        self.invulnerable_time: float = 0.0
        self.health: int = 3
        self.alive: bool = True
        
        # Visual properties
        self.vertices: List[Vector2] = [
            Vector2(0, -SHIP_SIZE),
            Vector2(-SHIP_SIZE * 0.7, SHIP_SIZE * 0.8),
            Vector2(0, SHIP_SIZE * 0.5),
            Vector2(SHIP_SIZE * 0.7, SHIP_SIZE * 0.8),
        ]
    
    def reset(self) -> None:
        """Reset ship to initial state."""
        super().reset()
        self.position = Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.max_speed = SHIP_MAX_SPEED
        self.fire_cooldown = 0.0
        self.fire_rate = 0.15
        self.damage = 1.0
        self.magnet_radius = 150.0
        self.invulnerable_time = 2.0
        self.health = 3
        self.alive = True
        self.velocity = Vector2(0, 0)
    
    def update(self, dt: float) -> None:
        """Update ship physics and state."""
        if not self.active or not self.alive:
            return
        
        # Update cooldowns
        if self.fire_cooldown > 0:
            self.fire_cooldown -= dt
        
        if self.invulnerable_time > 0:
            self.invulnerable_time -= dt
        
        # Apply friction
        self.apply_friction(SHIP_FRICTION, dt)
        
        # Clamp speed
        if self.velocity.length_squared() > self.max_speed ** 2:
            self.velocity.scale_to_length(self.max_speed)
        
        # Move and wrap
        self.move(dt)
        self.wrap_position()
    
    def thrust(self, dt: float) -> None:
        """Apply thrust in facing direction."""
        thrust_vector = Vector2(0, -1).rotate(self.rotation) * self.thrust_power * dt
        self.velocity += thrust_vector
    
    def rotate_left(self, dt: float) -> None:
        """Rotate ship counter-clockwise."""
        self.rotation -= SHIP_ROTATION_SPEED * dt
    
    def rotate_right(self, dt: float) -> None:
        """Rotate ship clockwise."""
        self.rotation += SHIP_ROTATION_SPEED * dt
    
    def can_fire(self) -> bool:
        """Check if ship can fire."""
        return self.fire_cooldown <= 0 and self.alive
    
    def fire(self) -> None:
        """Fire a bullet."""
        self.fire_cooldown = self.fire_rate
    
    def take_damage(self) -> bool:
        """Take damage. Returns True if hit (not invulnerable)."""
        if self.invulnerable_time > 0:
            return False
        self.health -= 1
        self.invulnerable_time = 2.0
        if self.health <= 0:
            self.alive = False
        return True
    
    def get_transformed_vertices(self) -> List[Vector2]:
        """Get vertices transformed by position and rotation."""
        transformed = []
        for v in self.vertices:
            rotated = v.rotate(self.rotation)
            transformed.append(rotated + self.position)
        return transformed
    
    def render(self, surface: pygame.Surface, camera_offset: Vector2) -> None:
        """Render the ship."""
        if not self.active or not self.alive:
            return
        
        # Blink when invulnerable
        if self.invulnerable_time > 0:
            alpha = int(255 * (0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.02)))
        else:
            alpha = 255
        
        vertices = self.get_transformed_vertices()
        screen_vertices = [(v.x - camera_offset.x, v.y - camera_offset.y) for v in vertices]
        
        # Draw ship outline
        pygame.draw.polygon(surface, COLOR_CYAN, screen_vertices, 2)
        
        # Draw inner triangle for style
        inner_vertices = [v * 0.6 for v in vertices]
        inner_screen = [(v.x - camera_offset.x, v.y - camera_offset.y) for v in inner_vertices]
        pygame.draw.polygon(surface, COLOR_CYAN, inner_screen, 1)


class Bullet(GameObject):
    """Projectile fired by the player."""
    
    def __init__(self) -> None:
        super().__init__()
        self.lifetime: float = BULLET_LIFETIME
        self.radius: float = BULLET_RADIUS
        self.damage: float = 1.0
    
    def reset(self) -> None:
        """Reset bullet for reuse."""
        super().reset()
        self.lifetime = BULLET_LIFETIME
        self.radius = BULLET_RADIUS
        self.damage = 1.0
    
    def update(self, dt: float) -> None:
        """Update bullet position and lifetime."""
        if not self.active:
            return
        
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.active = False
        
        self.move(dt)
        self.wrap_position()
    
    def render(self, surface: pygame.Surface, camera_offset: Vector2) -> None:
        """Render the bullet."""
        if not self.active:
            return
        
        pos = (self.position.x - camera_offset.x, self.position.y - camera_offset.y)
        
        # Draw glowing bullet
        pygame.draw.circle(surface, COLOR_YELLOW, (int(pos[0]), int(pos[1])), int(self.radius))
        
        # Outer glow
        pygame.draw.circle(surface, COLOR_ORANGE, (int(pos[0]), int(pos[1])), int(self.radius * 1.5), 1)


class AsteroidSize(Enum):
    """Enumeration of asteroid sizes."""
    LARGE = auto()
    MEDIUM = auto()
    SMALL = auto()


class Asteroid(GameObject):
    """Destructible asteroid that splits when hit."""
    
    def __init__(self) -> None:
        super().__init__()
        self.size: AsteroidSize = AsteroidSize.LARGE
        self.radius: float = ASTEROID_LARGE_RADIUS
        self.health: int = ASTEROID_LARGE_HP
        self.max_health: int = ASTEROID_LARGE_HP
        self.points: int = 100
        self.core_fragments: int = 1
        
        # Generate random polygon shape
        self.vertex_count: int = random.randint(8, 12)
        self.shape_offsets: List[float] = []
        self._generate_shape()
    
    def _generate_shape(self) -> None:
        """Generate irregular polygon shape for asteroid."""
        self.shape_offsets = []
        for i in range(self.vertex_count):
            angle = (i / self.vertex_count) * 360
            offset = random.uniform(0.8, 1.2)
            self.shape_offsets.append((angle, offset))
    
    def setup(self, size: AsteroidSize, position: Optional[Vector2] = None, 
              velocity: Optional[Vector2] = None) -> None:
        """Setup asteroid with specific parameters."""
        self.active = True
        self.size = size
        
        if size == AsteroidSize.LARGE:
            self.radius = ASTEROID_LARGE_RADIUS
            self.health = ASTEROID_LARGE_HP
            self.max_health = ASTEROID_LARGE_HP
            self.points = 100
            self.core_fragments = 1
        elif size == AsteroidSize.MEDIUM:
            self.radius = ASTEROID_MEDIUM_RADIUS
            self.health = ASTEROID_MEDIUM_HP
            self.max_health = ASTEROID_MEDIUM_HP
            self.points = 200
            self.core_fragments = 2
        else:  # SMALL
            self.radius = ASTEROID_SMALL_RADIUS
            self.health = ASTEROID_SMALL_HP
            self.max_health = ASTEROID_SMALL_HP
            self.points = 300
            self.core_fragments = 3
        
        if position:
            self.position = position.copy()
        else:
            # Spawn at edge of screen
            side = random.randint(0, 3)
            if side == 0:  # Top
                self.position = Vector2(random.uniform(0, SCREEN_WIDTH), -self.radius)
            elif side == 1:  # Right
                self.position = Vector2(SCREEN_WIDTH + self.radius, random.uniform(0, SCREEN_HEIGHT))
            elif side == 2:  # Bottom
                self.position = Vector2(random.uniform(0, SCREEN_WIDTH), SCREEN_HEIGHT + self.radius)
            else:  # Left
                self.position = Vector2(-self.radius, random.uniform(0, SCREEN_HEIGHT))
        
        if velocity:
            self.velocity = velocity.copy()
        else:
            # Random velocity towards center-ish
            angle = random.uniform(0, 360)
            speed = random.uniform(50, 150) * (size.value / 3 + 0.5)
            self.velocity = Vector2(math.cos(math.radians(angle)), math.sin(math.radians(angle))) * speed
        
        self.rotation = random.uniform(0, 360)
        self.angular_velocity = random.uniform(-30, 30)
    
    def reset(self) -> None:
        """Reset asteroid."""
        super().reset()
        self.size = AsteroidSize.LARGE
        self.radius = ASTEROID_LARGE_RADIUS
        self.health = ASTEROID_LARGE_HP
        self.max_health = ASTEROID_LARGE_HP
        self.points = 100
        self.core_fragments = 1
        self._generate_shape()
    
    def take_damage(self, damage: float) -> bool:
        """Take damage. Returns True if destroyed."""
        self.health -= int(damage)
        return self.health <= 0
    
    def get_shape_vertices(self) -> List[Vector2]:
        """Get transformed shape vertices."""
        vertices = []
        for angle_deg, offset in self.shape_offsets:
            angle_rad = math.radians(angle_deg + self.rotation)
            x = math.cos(angle_rad) * self.radius * offset
            y = math.sin(angle_rad) * self.radius * offset
            vertices.append(Vector2(x, y) + self.position)
        return vertices
    
    def update(self, dt: float) -> None:
        """Update asteroid."""
        if not self.active:
            return
        
        self.move(dt)
        self.wrap_position()
    
    def render(self, surface: pygame.Surface, camera_offset: Vector2) -> None:
        """Render asteroid with wireframe style."""
        if not self.active:
            return
        
        vertices = self.get_shape_vertices()
        screen_vertices = [(v.x - camera_offset.x, v.y - camera_offset.y) for v in vertices]
        
        # Color based on health
        health_ratio = self.health / self.max_health
        if health_ratio > 0.66:
            color = COLOR_WHITE
        elif health_ratio > 0.33:
            color = COLOR_ORANGE
        else:
            color = COLOR_RED
        
        # Draw outer polygon
        pygame.draw.polygon(surface, color, screen_vertices, 2)
        
        # Draw inner details
        if len(screen_vertices) > 3:
            inner_verts = []
            for i in range(0, len(screen_vertices) - 1, 2):
                mid = ((screen_vertices[i][0] + screen_vertices[i+1][0]) / 2,
                       (screen_vertices[i][1] + screen_vertices[i+1][1]) / 2)
                inner_verts.append(mid)
            if inner_verts:
                pygame.draw.polygon(surface, color, inner_verts, 1)


class Particle(GameObject):
    """Visual effect particle for explosions and thrusters."""
    
    def __init__(self) -> None:
        super().__init__()
        self.lifetime: float = PARTICLE_LIFETIME
        self.max_lifetime: float = PARTICLE_LIFETIME
        self.size: float = 3.0
        self.color: Tuple[int, int, int] = COLOR_ORANGE
        self.decay_rate: float = 1.0
    
    def reset(self) -> None:
        """Reset particle."""
        super().reset()
        self.lifetime = PARTICLE_LIFETIME
        self.max_lifetime = PARTICLE_LIFETIME
        self.size = 3.0
        self.color = COLOR_ORANGE
    
    def setup_explosion(self, position: Vector2, color: Tuple[int, int, int] = COLOR_ORANGE) -> None:
        """Setup as explosion particle."""
        self.active = True
        self.position = position.copy()
        angle = random.uniform(0, 360)
        speed = random.uniform(100, 400)
        self.velocity = Vector2(math.cos(math.radians(angle)), math.sin(math.radians(angle))) * speed
        self.lifetime = random.uniform(0.5, 1.0)
        self.max_lifetime = self.lifetime
        self.size = random.uniform(2, 5)
        self.color = color
        self.decay_rate = 1.0 / self.lifetime
    
    def setup_thruster(self, position: Vector2, direction: Vector2) -> None:
        """Setup as thruster particle."""
        self.active = True
        self.position = position.copy()
        spread = random.uniform(-0.3, 0.3)
        dir_vec = direction.rotate(math.degrees(spread))
        speed = random.uniform(100, 200)
        self.velocity = dir_vec * speed
        self.lifetime = random.uniform(0.2, 0.4)
        self.max_lifetime = self.lifetime
        self.size = random.uniform(3, 6)
        self.color = random.choice([COLOR_ORANGE, COLOR_YELLOW, COLOR_RED])
        self.decay_rate = 1.0 / self.lifetime
    
    def update(self, dt: float) -> None:
        """Update particle physics and lifetime."""
        if not self.active:
            return
        
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.active = False
            return
        
        # Apply drag
        self.velocity *= 0.95
        self.move(dt)
    
    def render(self, surface: pygame.Surface, camera_offset: Vector2) -> None:
        """Render particle with fade effect."""
        if not self.active:
            return
        
        alpha = self.lifetime / self.max_lifetime
        size = int(self.size * alpha)
        
        if size < 1:
            size = 1
        
        pos = (self.position.x - camera_offset.x, self.position.y - camera_offset.y)
        
        # Fade color
        faded_color = tuple(int(c * alpha) for c in self.color)
        
        pygame.draw.circle(surface, faded_color, (int(pos[0]), int(pos[1])), size)


class CoreFragment(GameObject):
    """Collectible currency dropped by asteroids."""
    
    def __init__(self) -> None:
        super().__init__()
        self.radius: float = 8.0
        self.value: int = 1
        self.magnetized: bool = False
        self.lifetime: float = 10.0  # Despawn after 10 seconds
    
    def reset(self) -> None:
        """Reset fragment."""
        super().reset()
        self.radius = 8.0
        self.value = 1
        self.magnetized = False
        self.lifetime = 10.0
    
    def setup(self, position: Vector2, value: int = 1) -> None:
        """Setup fragment."""
        self.active = True
        self.position = position.copy()
        self.value = value
        self.lifetime = 10.0
        
        # Random velocity
        angle = random.uniform(0, 360)
        speed = random.uniform(50, 150)
        self.velocity = Vector2(math.cos(math.radians(angle)), math.sin(math.radians(angle))) * speed
    
    def update(self, dt: float) -> None:
        """Update fragment."""
        if not self.active:
            return
        
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.active = False
            return
        
        # Apply friction
        self.velocity *= 0.98
        
        self.move(dt)
        self.wrap_position()
    
    def attract_to(self, target: Vector2, strength: float = 500.0) -> None:
        """Attract fragment towards target."""
        direction = target - self.position
        distance = direction.length()
        
        if distance > 0:
            direction.normalize_ip()
            force = strength / (distance + 1)
            self.velocity += direction * force * 0.016  # Scale for frame
    
    def render(self, surface: pygame.Surface, camera_offset: Vector2) -> None:
        """Render core fragment."""
        if not self.active:
            return
        
        pos = (self.position.x - camera_offset.x, self.position.y - camera_offset.y)
        
        # Draw diamond shape
        points = [
            (pos[0], pos[1] - self.radius),
            (pos[0] + self.radius, pos[1]),
            (pos[0], pos[1] + self.radius),
            (pos[0] - self.radius, pos[1]),
        ]
        
        pygame.draw.polygon(surface, COLOR_PURPLE, points, 2)
        
        # Inner glow
        inner_radius = self.radius * 0.5
        pygame.draw.circle(surface, COLOR_PURPLE, (int(pos[0]), int(pos[1])), int(inner_radius))


# =============================================================================
# CAMERA SHAKE SYSTEM
# =============================================================================


class CameraShake:
    """Screen shake effect with exponential decay."""
    
    def __init__(self) -> None:
        self.intensity: float = 0.0
        self.decay: float = 5.0
        self.offset: Vector2 = Vector2(0, 0)
    
    def add_shake(self, intensity: float) -> None:
        """Add shake intensity."""
        self.intensity = max(self.intensity, intensity)
    
    def update(self, dt: float) -> Vector2:
        """Update shake and return current offset."""
        if self.intensity > 0.1:
            self.offset.x = random.uniform(-self.intensity, self.intensity)
            self.offset.y = random.uniform(-self.intensity, self.intensity)
            self.intensity -= self.decay * dt
            if self.intensity < 0:
                self.intensity = 0
        else:
            self.offset = Vector2(0, 0)
        
        return self.offset
    
    def reset(self) -> None:
        """Reset shake."""
        self.intensity = 0.0
        self.offset = Vector2(0, 0)


# =============================================================================
# COMBO SYSTEM
# =============================================================================


class ComboSystem:
    """
    Combo system that tracks consecutive hits without misses.
    Increases score multiplier and provides visual feedback.
    """
    
    def __init__(self) -> None:
        self.combo_count: int = 0
        self.multiplier: float = 1.0
        self.timer: float = 0.0
        self.last_hit_time: float = 0.0
        self.pulse_intensity: float = 0.0
    
    def add_hit(self) -> None:
        """Record a successful hit."""
        self.combo_count += 1
        self.multiplier = min(1.0 + self.combo_count * COMBO_MULTIPLIER_STEP, MAX_COMBO_MULTIPLIER)
        self.timer = COMBO_DECAY_TIME
        self.pulse_intensity = 1.0
    
    def add_miss(self) -> None:
        """Record a miss (bullet off-screen)."""
        self.reset()
    
    def take_damage(self) -> None:
        """Reset combo on taking damage."""
        self.reset()
    
    def reset(self) -> None:
        """Reset combo counter."""
        self.combo_count = 0
        self.multiplier = 1.0
        self.timer = 0.0
    
    def update(self, dt: float) -> None:
        """Update combo timer and pulse animation."""
        if self.timer > 0:
            self.timer -= dt
            if self.timer <= 0:
                self.reset()
        
        # Pulse animation
        if self.pulse_intensity > 0:
            self.pulse_intensity -= dt * 3
            if self.pulse_intensity < 0:
                self.pulse_intensity = 0
    
    def get_pulse_scale(self) -> float:
        """Get current pulse scale for UI animation."""
        return 1.0 + self.pulse_intensity * 0.3
    
    def render(self, surface: pygame.Surface) -> None:
        """Render combo display."""
        if self.combo_count < 2:
            return
        
        font = pygame.font.Font(None, 48)
        scale = self.get_pulse_scale()
        
        # Pulsing color based on multiplier
        hue = min(self.multiplier * 60, 120)
        color = (255, int(255 - hue), int(hue))
        
        text = f"COMBO x{self.multiplier:.1f}"
        text_surface = font.render(text, True, color)
        
        # Center top
        rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, 60))
        
        # Scale effect
        if scale > 1.0:
            text_surface = pygame.transform.scale(text_surface, 
                (int(rect.width * scale), int(rect.height * scale)))
            rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, 60))
        
        surface.blit(text_surface, rect)
        
        # Combo count below
        small_font = pygame.font.Font(None, 32)
        count_text = f"{self.combo_count} HITS"
        count_surface = small_font.render(count_text, True, COLOR_WHITE)
        count_rect = count_surface.get_rect(center=(SCREEN_WIDTH // 2, 95))
        surface.blit(count_surface, count_rect)


# =============================================================================
# SHOP AND UPGRADES SYSTEM
# =============================================================================


class UpgradeType(Enum):
    """Types of available upgrades."""
    MAX_SPEED = "max_speed"
    FIRE_RATE = "fire_rate"
    DAMAGE = "damage"
    MAGNET_RADIUS = "magnet_radius"


@dataclass
class UpgradeData:
    """Data for an upgrade."""
    name: str
    description: str
    upgrade_type: UpgradeType
    level: int = 0
    max_level: int = 5


class ShopSystem:
    """Shop system for purchasing permanent upgrades."""
    
    def __init__(self) -> None:
        self.currency: int = 0
        self.upgrades: Dict[UpgradeType, UpgradeData] = {
            UpgradeType.MAX_SPEED: UpgradeData(
                name="Engine Boost",
                description="Increase maximum ship speed",
                upgrade_type=UpgradeType.MAX_SPEED,
            ),
            UpgradeType.FIRE_RATE: UpgradeData(
                name="Rapid Fire",
                description="Reduce weapon cooldown",
                upgrade_type=UpgradeType.FIRE_RATE,
            ),
            UpgradeType.DAMAGE: UpgradeData(
                name="Plasma Charge",
                description="Increase bullet damage",
                upgrade_type=UpgradeType.DAMAGE,
            ),
            UpgradeType.MAGNET_RADIUS: UpgradeData(
                name="Core Magnet",
                description="Increase fragment pickup range",
                upgrade_type=UpgradeType.MAGNET_RADIUS,
            ),
        }
    
    def get_upgrade_cost(self, upgrade_type: UpgradeType) -> int:
        """Get cost for next level of upgrade."""
        upgrade = self.upgrades[upgrade_type]
        if upgrade.level >= upgrade.max_level:
            return 0
        
        costs = UPGRADE_COSTS[upgrade_type.value]
        return costs[upgrade.level]
    
    def can_afford(self, upgrade_type: UpgradeType) -> bool:
        """Check if player can afford upgrade."""
        cost = self.get_upgrade_cost(upgrade_type)
        return self.currency >= cost and cost > 0
    
    def purchase(self, upgrade_type: UpgradeType) -> bool:
        """Purchase upgrade. Returns True if successful."""
        cost = self.get_upgrade_cost(upgrade_type)
        if cost <= 0 or self.currency < cost:
            return False
        
        upgrade = self.upgrades[upgrade_type]
        if upgrade.level >= upgrade.max_level:
            return False
        
        self.currency -= cost
        upgrade.level += 1
        return True
    
    def get_stats_multiplier(self, upgrade_type: UpgradeType) -> float:
        """Get stat multiplier based on upgrade level."""
        upgrade = self.upgrades[upgrade_type]
        level = upgrade.level
        
        multipliers = {
            UpgradeType.MAX_SPEED: 1.0 + level * 0.15,
            UpgradeType.FIRE_RATE: 1.0 / (1.0 + level * 0.12),
            UpgradeType.DAMAGE: 1.0 + level * 0.25,
            UpgradeType.MAGNET_RADIUS: 1.0 + level * 0.3,
        }
        
        return multipliers[upgrade_type]
    
    def is_maxed(self, upgrade_type: UpgradeType) -> bool:
        """Check if upgrade is maxed out."""
        return self.upgrades[upgrade_type].level >= self.upgrades[upgrade_type].max_level
    
    def render(self, surface: pygame.Surface) -> None:
        """Render shop UI."""
        # Background overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))
        
        # Title
        title_font = pygame.font.Font(None, 72)
        title = title_font.render("UPGRADE STATION", True, COLOR_CYAN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 80))
        surface.blit(title, title_rect)
        
        # Currency display
        currency_font = pygame.font.Font(None, 48)
        currency_text = currency_font.render(f"Core Fragments: {self.currency}", True, COLOR_PURPLE)
        currency_rect = currency_text.get_rect(center=(SCREEN_WIDTH // 2, 140))
        surface.blit(currency_text, currency_rect)
        
        # Upgrades
        y_offset = 220
        item_font = pygame.font.Font(None, 36)
        small_font = pygame.font.Font(None, 28)
        
        for upgrade_type, upgrade in self.upgrades.items():
            cost = self.get_upgrade_cost(upgrade_type)
            can_afford = self.can_afford(upgrade_type)
            is_maxed = self.is_maxed(upgrade_type)
            
            # Item background
            item_bg = pygame.Rect(SCREEN_WIDTH // 2 - 300, y_offset, 600, 80)
            pygame.draw.rect(surface, COLOR_WHITE, item_bg, 2)
            
            # Name and level
            name_text = f"{upgrade.name} (Lv.{upgrade.level}/{upgrade.max_level})"
            name_surface = item_font.render(name_text, True, COLOR_WHITE)
            surface.blit(name_surface, (item_bg.x + 20, item_bg.y + 10))
            
            # Description
            desc_surface = small_font.render(upgrade.description, True, COLOR_CYAN)
            surface.blit(desc_surface, (item_bg.x + 20, item_bg.y + 40))
            
            # Cost or MAX label
            if is_maxed:
                max_surface = small_font.render("MAXED", True, COLOR_GREEN)
                surface.blit(max_surface, (item_bg.right - 100, item_bg.y + 30))
            else:
                cost_color = COLOR_GREEN if can_afford else COLOR_RED
                cost_surface = small_font.render(f"Cost: {cost}", True, cost_color)
                surface.blit(cost_surface, (item_bg.right - 150, item_bg.y + 30))
            
            y_offset += 100
        
        # Instructions
        inst_font = pygame.font.Font(None, 32)
        inst_text = "Press 1-4 to purchase | Press ENTER to start game"
        inst_surface = inst_font.render(inst_text, True, COLOR_WHITE)
        inst_rect = inst_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        surface.blit(inst_surface, inst_rect)


# =============================================================================
# GAME STATE MANAGEMENT
# =============================================================================


class GameState(Enum):
    """Game state enumeration."""
    MENU = auto()
    PLAYING = auto()
    SHOP = auto()
    GAME_OVER = auto()


class GameManager:
    """
    Main game manager handling state transitions, entity pools,
    and coordinating all game systems.
    """
    
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("NEON ASTEROIDS - Production Edition")
        self.screen: pygame.Surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.running: bool = True
        
        # Game state
        self.state: GameState = GameState.MENU
        self.score: int = 0
        self.wave: int = 1
        self.total_currency_earned: int = 0
        
        # Systems
        self.shop: ShopSystem = ShopSystem()
        self.combo: ComboSystem = ComboSystem()
        self.camera_shake: CameraShake = CameraShake()
        self.spatial_grid: SpatialGrid = SpatialGrid()
        
        # Object pools
        self.bullet_pool: ObjectPool[Bullet] = ObjectPool(Bullet, initial_size=50)
        self.asteroid_pool: ObjectPool[Asteroid] = ObjectPool(Asteroid, initial_size=30)
        self.particle_pool: ObjectPool[Particle] = ObjectPool(Particle, initial_size=500)
        self.fragment_pool: ObjectPool[CoreFragment] = ObjectPool(CoreFragment, initial_size=100)
        
        # Player ship
        self.ship: Ship = Ship()
        self.ship.active = True
        
        # Wave management
        self.asteroids_remaining: int = 0
        self.wave_delay: float = 0.0
        
        # Input state
        self.keys_pressed: Set[int] = set()
        
        # Fonts
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
    
    def start_new_game(self) -> None:
        """Initialize a new game session."""
        self.score = 0
        self.wave = 1
        self.total_currency_earned = 0
        self.shop.currency = 0
        
        # Reset ship with upgrades
        self.ship.reset()
        self.apply_upgrades_to_ship()
        
        # Clear pools
        self.bullet_pool.release_all()
        self.asteroid_pool.release_all()
        self.particle_pool.release_all()
        self.fragment_pool.release_all()
        
        # Start first wave
        self.start_wave()
        
        self.state = GameState.PLAYING
        self.combo.reset()
        self.camera_shake.reset()
    
    def apply_upgrades_to_ship(self) -> None:
        """Apply shop upgrades to ship stats."""
        self.ship.max_speed = SHIP_MAX_SPEED * self.shop.get_stats_multiplier(UpgradeType.MAX_SPEED)
        self.ship.fire_rate = 0.15 * self.shop.get_stats_multiplier(UpgradeType.FIRE_RATE)
        self.ship.damage = 1.0 * self.shop.get_stats_multiplier(UpgradeType.DAMAGE)
        self.ship.magnet_radius = 150.0 * self.shop.get_stats_multiplier(UpgradeType.MAGNET_RADIUS)
    
    def start_wave(self) -> None:
        """Start a new wave of asteroids."""
        self.asteroids_remaining = 3 + self.wave * 2
        
        for _ in range(min(self.asteroids_remaining, 5)):
            asteroid = self.asteroid_pool.acquire()
            if asteroid and isinstance(asteroid, Asteroid):
                asteroid.setup(AsteroidSize.LARGE)
        
        self.asteroids_remaining = max(self.asteroids_remaining - 5, 0)
    
    def spawn_asteroid_split(self, asteroid: Asteroid) -> None:
        """Spawn smaller asteroids when one is destroyed."""
        if asteroid.size == AsteroidSize.LARGE:
            new_size = AsteroidSize.MEDIUM
            count = random.randint(2, 3)
        elif asteroid.size == AsteroidSize.MEDIUM:
            new_size = AsteroidSize.SMALL
            count = random.randint(2, 3)
        else:
            return  # Small asteroids don't split
        
        for _ in range(count):
            new_asteroid = self.asteroid_pool.acquire()
            if new_asteroid and isinstance(new_asteroid, Asteroid):
                new_asteroid.setup(new_size, asteroid.position.copy(), asteroid.velocity.copy())
    
    def spawn_particles(self, position: Vector2, count: int, 
                       color: Tuple[int, int, int] = COLOR_ORANGE) -> None:
        """Spawn explosion particles."""
        for _ in range(count):
            particle = self.particle_pool.acquire()
            if particle and isinstance(particle, Particle):
                particle.setup_explosion(position, color)
    
    def spawn_thruster_particles(self) -> None:
        """Spawn thruster particles behind ship."""
        if not self.ship.alive:
            return
        
        # Get rear position of ship
        rear_offset = Vector2(0, SHIP_SIZE * 0.8).rotate(self.ship.rotation)
        rear_pos = self.ship.position + rear_offset
        
        particle = self.particle_pool.acquire()
        if particle and isinstance(particle, Particle):
            back_direction = Vector2(0, 1).rotate(self.ship.rotation)
            particle.setup_thruster(rear_pos, back_direction)
    
    def spawn_core_fragment(self, position: Vector2, value: int) -> None:
        """Spawn collectible core fragment."""
        fragment = self.fragment_pool.acquire()
        if fragment and isinstance(fragment, CoreFragment):
            fragment.setup(position, value)
    
    def check_collisions(self) -> None:
        """Check and handle all collisions using spatial grid."""
        # Build spatial grid for active objects
        self.spatial_grid.clear()
        
        all_objects: List[GameObject] = []
        
        # Add bullets
        for bullet in self.bullet_pool.get_active():
            self.spatial_grid.insert(bullet.id, bullet.position)
            all_objects.append(bullet)
        
        # Add asteroids
        for asteroid in self.asteroid_pool.get_active():
            self.spatial_grid.insert(asteroid.id, asteroid.position)
            all_objects.append(asteroid)
        
        # Add fragments
        for fragment in self.fragment_pool.get_active():
            self.spatial_grid.insert(fragment.id, fragment.position)
            all_objects.append(fragment)
        
        # Add ship
        if self.ship.active and self.ship.alive:
            self.spatial_grid.insert(self.ship.id, self.ship.position)
            all_objects.append(self.ship)
        
        # Check bullet-asteroid collisions
        for bullet in self.bullet_pool.get_active():
            nearby = self.spatial_grid.get_nearby(bullet.position, bullet.radius + ASTEROID_LARGE_RADIUS)
            
            for asteroid in self.asteroid_pool.get_active():
                if asteroid.id not in nearby:
                    continue
                
                # Circle collision check
                dx = bullet.position.x - asteroid.position.x
                dy = bullet.position.y - asteroid.position.y
                distance_sq = dx * dx + dy * dy
                min_dist = bullet.radius + asteroid.radius
                
                if distance_sq < min_dist * min_dist:
                    # Hit!
                    destroyed = asteroid.take_damage(self.ship.damage)
                    self.bullet_pool.release(bullet)
                    
                    # Spawn particles
                    self.spawn_particles(bullet.position.copy(), 10, COLOR_YELLOW)
                    
                    if destroyed:
                        self.handle_asteroid_destroyed(asteroid)
                    
                    self.combo.add_hit()
                    break
        
        # Check ship-asteroid collisions
        if self.ship.active and self.ship.alive:
            for asteroid in self.asteroid_pool.get_active():
                dx = self.ship.position.x - asteroid.position.x
                dy = self.ship.position.y - asteroid.position.y
                distance_sq = dx * dx + dy * dy
                min_dist = SHIP_SIZE + asteroid.radius
                
                if distance_sq < min_dist * min_dist:
                    if self.ship.take_damage():
                        self.combo.take_damage()
                        self.camera_shake.add_shake(15)
                        self.spawn_particles(self.ship.position.copy(), 30, COLOR_RED)
                        
                        if not self.ship.alive:
                            self.handle_game_over()
    
    def handle_asteroid_destroyed(self, asteroid: Asteroid) -> None:
        """Handle asteroid destruction logic."""
        # Score with combo multiplier
        points = int(asteroid.points * self.combo.multiplier)
        self.score += points
        
        # Spawn fragments (currency)
        fragments = asteroid.core_fragments
        for _ in range(fragments):
            self.spawn_core_fragment(asteroid.position.copy(), 1)
        
        # Spawn particles
        self.spawn_particles(asteroid.position.copy(), 20, COLOR_WHITE)
        
        # Camera shake for large asteroids
        if asteroid.size == AsteroidSize.LARGE:
            self.camera_shake.add_shake(8)
        
        # Split asteroid
        self.spawn_asteroid_split(asteroid)
        
        # Release asteroid
        self.asteroid_pool.release(asteroid)
        
        # Check wave completion
        if len(self.asteroid_pool.get_active()) == 0 and self.asteroids_remaining == 0:
            self.wave_complete()
    
    def wave_complete(self) -> None:
        """Handle wave completion."""
        self.wave += 1
        self.wave_delay = 2.0
        
        # Bonus currency for wave completion
        bonus = self.wave * 10
        self.shop.currency += bonus
        self.total_currency_earned += bonus
    
    def handle_game_over(self) -> None:
        """Handle game over state."""
        self.state = GameState.GAME_OVER
    
    def collect_fragments(self) -> None:
        """Handle fragment collection by ship."""
        if not self.ship.alive:
            return
        
        for fragment in self.fragment_pool.get_active():
            distance = fragment.position.distance_to(self.ship.position)
            
            # Magnet effect
            if distance < self.ship.magnet_radius:
                fragment.attract_to(self.ship.position)
                fragment.magnetized = True
            
            # Collection
            if distance < SHIP_SIZE + fragment.radius:
                self.shop.currency += fragment.value
                self.total_currency_earned += fragment.value
                self.fragment_pool.release(fragment)
                
                # Small sparkle effect
                self.spawn_particles(fragment.position.copy(), 5, COLOR_PURPLE)
    
    def handle_input(self, dt: float) -> None:
        """Process player input."""
        if self.state != GameState.PLAYING:
            return
        
        # Rotation
        if pygame.K_LEFT in self.keys_pressed or pygame.K_a in self.keys_pressed:
            self.ship.rotate_left(dt)
        if pygame.K_RIGHT in self.keys_pressed or pygame.K_d in self.keys_pressed:
            self.ship.rotate_right(dt)
        
        # Thrust
        if pygame.K_UP in self.keys_pressed or pygame.K_w in self.keys_pressed:
            self.ship.thrust(dt)
            self.spawn_thruster_particles()
        
        # Fire
        if pygame.K_SPACE in self.keys_pressed:
            if self.ship.can_fire():
                self.ship.fire()
                
                # Spawn bullet
                bullet = self.bullet_pool.acquire()
                if bullet and isinstance(bullet, Bullet):
                    bullet.position = self.ship.position.copy()
                    bullet.damage = self.ship.damage
                    
                    # Calculate bullet velocity from ship velocity + direction
                    direction = Vector2(0, -1).rotate(self.ship.rotation)
                    bullet.velocity = direction * BULLET_SPEED + self.ship.velocity * 0.5
    
    def update_bullets_off_screen(self) -> None:
        """Check for bullets that went off screen (combo breaker)."""
        for bullet in list(self.bullet_pool.get_active()):
            if (bullet.position.x < -BULLET_RADIUS or 
                bullet.position.x > SCREEN_WIDTH + BULLET_RADIUS or
                bullet.position.y < -BULLET_RADIUS or 
                bullet.position.y > SCREEN_HEIGHT + BULLET_RADIUS):
                
                # Only count as miss if it lived long enough
                if bullet.lifetime < BULLET_LIFETIME - 0.3:
                    self.combo.add_miss()
                self.bullet_pool.release(bullet)
    
    def run(self) -> None:
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time in seconds
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                elif event.type == pygame.KEYDOWN:
                    self.keys_pressed.add(event.key)
                    
                    if self.state == GameState.MENU:
                        if event.key == pygame.K_RETURN:
                            self.start_new_game()
                        elif event.key == pygame.K_ESCAPE:
                            self.running = False
                    
                    elif self.state == GameState.PLAYING:
                        if event.key == pygame.K_ESCAPE:
                            self.state = GameState.SHOP
                    
                    elif self.state == GameState.SHOP:
                        if event.key == pygame.K_RETURN:
                            self.apply_upgrades_to_ship()
                            self.start_wave()
                            self.state = GameState.PLAYING
                        elif event.key == pygame.K_1:
                            self.shop.purchase(UpgradeType.MAX_SPEED)
                        elif event.key == pygame.K_2:
                            self.shop.purchase(UpgradeType.FIRE_RATE)
                        elif event.key == pygame.K_3:
                            self.shop.purchase(UpgradeType.DAMAGE)
                        elif event.key == pygame.K_4:
                            self.shop.purchase(UpgradeType.MAGNET_RADIUS)
                    
                    elif self.state == GameState.GAME_OVER:
                        if event.key == pygame.K_RETURN:
                            self.state = GameState.SHOP
                        elif event.key == pygame.K_ESCAPE:
                            self.state = GameState.MENU
                
                elif event.type == pygame.KEYUP:
                    self.keys_pressed.discard(event.key)
            
            # Update based on state
            if self.state == GameState.PLAYING:
                self.update_game(dt)
            elif self.state == GameState.SHOP:
                pass  # Shop is static, just rendering
            elif self.state == GameState.GAME_OVER:
                pass  # Game over screen is static
            
            # Render
            self.render()
            
            pygame.display.flip()
        
        pygame.quit()
    
    def update_game(self, dt: float) -> None:
        """Update game logic during playing state."""
        # Update ship
        self.ship.update(dt)
        
        # Update pools
        self.bullet_pool.update(dt)
        self.asteroid_pool.update(dt)
        self.particle_pool.update(dt)
        self.fragment_pool.update(dt)
        
        # Handle input
        self.handle_input(dt)
        
        # Check collisions
        self.check_collisions()
        
        # Collect fragments
        self.collect_fragments()
        
        # Check bullets off screen
        self.update_bullets_off_screen()
        
        # Update systems
        self.combo.update(dt)
        camera_offset = self.camera_shake.update(dt)
        
        # Wave management
        if self.wave_delay > 0:
            self.wave_delay -= dt
            if self.wave_delay <= 0:
                self.start_wave()
        
        # Spawn additional asteroids periodically
        if len(self.asteroid_pool.get_active()) < 3 and self.asteroids_remaining > 0:
            if random.random() < 0.02:  # 2% chance per frame
                asteroid = self.asteroid_pool.acquire()
                if asteroid and isinstance(asteroid, Asteroid):
                    asteroid.setup(AsteroidSize.LARGE)
                    self.asteroids_remaining -= 1
    
    def render(self) -> None:
        """Render the game."""
        # Clear screen
        self.screen.fill(COLOR_BLACK)
        
        camera_offset = self.camera_shake.offset
        
        if self.state == GameState.PLAYING:
            self.render_game(camera_offset)
        elif self.state == GameState.MENU:
            self.render_menu()
        elif self.state == GameState.SHOP:
            self.render_shop()
        elif self.state == GameState.GAME_OVER:
            self.render_game_over()
        
        # Always render UI on top
        if self.state == GameState.PLAYING:
            self.render_ui()
    
    def render_game(self, camera_offset: Vector2) -> None:
        """Render game world."""
        # Render all active objects
        self.bullet_pool.render_all(self.screen, camera_offset)
        self.asteroid_pool.render_all(self.screen, camera_offset)
        self.fragment_pool.render_all(self.screen, camera_offset)
        self.particle_pool.render_all(self.screen, camera_offset)
        
        # Render ship
        self.ship.render(self.screen, camera_offset)
    
    def render_ui(self) -> None:
        """Render HUD elements."""
        # Score
        score_text = self.font_small.render(f"Score: {self.score}", True, COLOR_WHITE)
        self.screen.blit(score_text, (20, 20))
        
        # Wave
        wave_text = self.font_small.render(f"Wave: {self.wave}", True, COLOR_CYAN)
        self.screen.blit(wave_text, (20, 50))
        
        # Currency
        currency_text = self.font_small.render(f"Fragments: {self.shop.currency}", True, COLOR_PURPLE)
        self.screen.blit(currency_text, (20, 80))
        
        # Health
        health_text = self.font_small.render(f"Health: {'♥' * self.ship.health}", True, COLOR_RED)
        self.screen.blit(health_text, (20, 110))
        
        # Combo
        self.combo.render(self.screen)
        
        # Upgrade hints
        hint_text = self.font_small.render("ESC - Shop", True, COLOR_WHITE)
        self.screen.blit(hint_text, (SCREEN_WIDTH - 150, 20))
    
    def render_menu(self) -> None:
        """Render main menu."""
        title = self.font_large.render("NEON ASTEROIDS", True, COLOR_CYAN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(title, title_rect)
        
        subtitle = self.font_medium.render("Production Edition", True, COLOR_WHITE)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
        self.screen.blit(subtitle, subtitle_rect)
        
        instructions = self.font_small.render("Press ENTER to Start | ESC to Quit", True, COLOR_YELLOW)
        inst_rect = instructions.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
        self.screen.blit(instructions, inst_rect)
        
        # Controls info
        controls = [
            "Controls:",
            "WASD / Arrows - Move",
            "SPACE - Fire",
            "ESC - Shop"
        ]
        
        y_offset = SCREEN_HEIGHT // 2 + 150
        for line in controls:
            text = self.font_small.render(line, True, COLOR_WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            self.screen.blit(text, text_rect)
            y_offset += 35
    
    def render_shop(self) -> None:
        """Render shop screen."""
        self.shop.render(self.screen)
    
    def render_game_over(self) -> None:
        """Render game over screen."""
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        game_over = self.font_large.render("GAME OVER", True, COLOR_RED)
        go_rect = game_over.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(game_over, go_rect)
        
        final_score = self.font_medium.render(f"Final Score: {self.score}", True, COLOR_WHITE)
        fs_rect = final_score.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(final_score, fs_rect)
        
        wave_reached = self.font_medium.render(f"Wave Reached: {self.wave}", True, COLOR_CYAN)
        wr_rect = wave_reached.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70))
        self.screen.blit(wave_reached, wr_rect)
        
        currency_earned = self.font_small.render(f"Total Fragments Earned: {self.total_currency_earned}", True, COLOR_PURPLE)
        ce_rect = currency_earned.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 130))
        self.screen.blit(currency_earned, ce_rect)
        
        continue_text = self.font_small.render("Press ENTER for Shop | ESC for Menu", True, COLOR_YELLOW)
        ct_rect = continue_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 200))
        self.screen.blit(continue_text, ct_rect)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


def main() -> None:
    """Main entry point."""
    game = GameManager()
    game.run()


if __name__ == "__main__":
    main()
