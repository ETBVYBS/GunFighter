import sys
import pygame
import random
import math
# basic top-level imports for system, pygame, and randomness
#import time
#import json

# Base gun class for weapon system
class Gun:
    """Base class for all weapons"""
    def __init__(self, name, max_ammo, fire_rate):
        self.name = name
        self.ammo = 0
        self.max_ammo = max_ammo  # max ammo per pickup
        self.fire_rate = fire_rate  # frames between shots
        self.cooldown = 0  # current cooldown counter
    
    def can_fire(self):
        """Check if weapon is ready to fire"""
        return self.cooldown <= 0 and self.ammo > 0
    
    def update(self, pos=None, direction=None):
        """Update weapon state each frame. By default, just decrement cooldown.

        Subclasses may return a list of additional bullets to spawn (e.g. for
        rifle bursts). The parameters `pos`/`direction` are provided so that
        weapons can generate bullets from the player's current position if
        needed.
        """
        self.cooldown = max(0, self.cooldown - 1)
        return []
    
    def fire(self, pos, direction):
        """Fire the weapon, returns list of bullets"""
        raise NotImplementedError


class Pistol(Gun):
    """Basic pistol - single shot, fast fire rate"""
    def __init__(self):
        super().__init__("Pistol", 999, 10)  # unlimited ammo effectively
        self.ammo = 999
    
    def fire(self, pos, direction):
        """Fire a single bullet"""
        self.ammo -= 1
        self.cooldown = self.fire_rate
        bullet = Bullet(pos[0], pos[1], direction, from_player=True)
        return [bullet]


class Shotgun(Gun):
    """Shotgun - cone of 5-7 bullets, slower fire rate"""
    def __init__(self):
        super().__init__("Shotgun", 12, 30)  # 12 shots per pickup, 30 frame cooldown
        self.ammo = 0
    
    def fire(self, pos, direction):
        """Fire a cone of bullets"""
        self.ammo -= 1
        self.cooldown = self.fire_rate
        bullets = []
        num_bullets = random.randint(5, 7)
        spread_angle = 60  # degrees
        base_angle = math.atan2(direction[1], direction[0])
        
        for i in range(num_bullets):
            angle_offset = (spread_angle / (num_bullets - 1)) * (i - (num_bullets - 1) / 2) * (math.pi / 180)
            angle = base_angle + angle_offset
            direction_spread = (math.cos(angle), math.sin(angle))
            bullet = Bullet(pos[0], pos[1], direction_spread, from_player=True)
            bullets.append(bullet)
        
        return bullets


class Rifle(Gun):
    """Three-burst rifle - fires three quick shots per trigger pull"""
    def __init__(self):
        super().__init__("Rifle", 24, 20)  # 24 shots per pickup, 20 frame cooldown
        self.ammo = 0
        # burst state: after firing one bullet, we queue two more
        self.burst_remaining = 0
        # frames to wait between burst bullets (lower => faster sequence)
        self.burst_interval = 3
        self.burst_timer = 0
    
    def fire(self, pos, direction):
        """Fire the first bullet of a three-shot burst. Subsequent shots are
        produced by update() over the next few frames so they appear spaced
        out instead of all at once.
        """
        if self.ammo <= 0:
            return []
        self.ammo -= 1
        self.cooldown = self.fire_rate
        # schedule the remaining two bullets
        self.burst_remaining = 2
        self.burst_timer = self.burst_interval
        return [Bullet(pos[0], pos[1], direction, from_player=True)]
    
    def update(self, pos=None, direction=None):
        # always decrement base cooldown
        super().update(pos, direction)
        bullets = []
        if self.burst_timer > 0:
            self.burst_timer -= 1
        elif self.burst_remaining > 0 and pos is not None and direction is not None:
            # fire next bullet in burst
            self.burst_remaining -= 1
            bullets.append(Bullet(pos[0], pos[1], direction, from_player=True))
            self.burst_timer = self.burst_interval
        return bullets

# Player character class handles movement, rendering, and collision with walls
class Player:
    player_size = 20
    player_speed = 4
    speed = player_speed
    player_colour = (0, 0, 255)


    def __init__(self, x, y, walls):
        # initialize player rectangle position, lives, and movement attributes
        self.rect = pygame.Rect(x, y, Player.player_size, Player.player_size)
        self.lives = 3
        self.health = 100  # current health
        self.max_health = 100  # maximum health
        # Weapon system
        self.pistol = Pistol()
        self.rifle = Rifle()
        self.shotgun = Shotgun()
        self.weapons = [self.pistol, self.rifle, self.shotgun]
        self.current_weapon_index = 0  # Start with pistol
        #print(f"Player starting at: ({self.rect.x}, {self.rect.y}")
        self.walls = walls
        self.movement_y = 0
        self.movement_x = 0
        self.facing_direction = (0, -1)  # Default facing up

    def move(self, dx, dy,):
        # attempt to move player by dx/dy, checking for wall collisions per axis
        #print(f"dx: {dx}, dy: {dy}")
        new_rect = self.rect.copy()
        new_rect.x += dx
        if new_rect.collidelist(self.walls) == -1:
            self.rect.x += dx
        else:
            dx = 0

        new_rect.y += dy
        if new_rect.collidelist(self.walls) == -1:
            self.rect.y += dy
        else:
            dy = 0

        return dx, dy


    def handle_imput(self, keys):
        # read keyboard state and set movement and facing direction accordingly
        # movement is controlled with arrow keys; aiming is done with WASD
        self.movement_x, self.movement_y = 0, 0
        if keys[pygame.K_UP]:
            self.movement_y -= Player.player_speed
        if keys[pygame.K_DOWN]:
            self.movement_y += Player.player_speed
        if keys[pygame.K_LEFT]:
            self.movement_x -= Player.player_speed
        if keys[pygame.K_RIGHT]:
            self.movement_x += Player.player_speed
        
        # aim controls (do not move player)
        aim_x = 0
        aim_y = 0
        if keys[pygame.K_w]:
            aim_y -= 1
        if keys[pygame.K_s]:
            aim_y += 1
        if keys[pygame.K_a]:
            aim_x -= 1
        if keys[pygame.K_d]:
            aim_x += 1

        # update facing direction: aim keys take precedence
        if aim_x != 0 or aim_y != 0:
            # normalize each component to -1/0/1 so diagonal aiming works
            dir_x = aim_x / abs(aim_x) if aim_x != 0 else 0
            dir_y = aim_y / abs(aim_y) if aim_y != 0 else 0
            self.facing_direction = (dir_x, dir_y)
        elif self.movement_x != 0 or self.movement_y != 0:
            dir_x = self.movement_x / abs(self.movement_x) if self.movement_x != 0 else 0
            dir_y = self.movement_y / abs(self.movement_y) if self.movement_y != 0 else 0
            self.facing_direction = (dir_x, dir_y)
        
        if keys [pygame.K_ESCAPE]:
            pygame.quit()
            sys.exit()

    def draw(self, screen, colour=None):
        # draw the player rectangle on given screen (optional override colour)
        if colour is None:
            pygame.draw.rect(screen, Player.player_colour, self.rect)
        else:
            pygame.draw.rect(screen, colour, self.rect)

    def move_player(self, pos, dx, dy):
        # alternative movement logic that tests collisions without modifying self
        new_pos = pos.copy()

        # Checks for collision on x-axis
        new_pos[0] += dx
        player_rect = pygame.Rect(*new_pos, Player.player_size, Player.player_size)
        if player_rect.collidelist(self.walls) != -1:  # collision check with walls
            new_pos[0] -= dx

        # Checks for collision on y-axis
        new_pos[1] += dy
        player_rect = pygame.Rect(*new_pos, Player.player_size, Player.player_size)
        if player_rect.collidelist(self.walls) != -1:  # collision check with walls
            new_pos[1] -= dy

        return new_pos

    def change_lives(self, change):
        # adjust player life count, ensuring non-negative
        self.lives += change
        if self.lives <0:
            self.lives = 0

    def take_damage(self, amount):
        """Reduce health by amount, game ends when health reaches 0"""
        self.health -= amount
        if self.health < 0:
            self.health = 0

    def heal(self, amount):
        """Increase health up to max_health"""
        self.health = min(self.health + amount, self.max_health)

    def get_current_weapon(self):
        """Return the currently equipped weapon"""
        return self.weapons[self.current_weapon_index]
    
    def cycle_weapon(self):
        """Switch to the next weapon in the list"""
        self.current_weapon_index = (self.current_weapon_index + 1) % len(self.weapons)
        print(f"Switched to {self.get_current_weapon().name}")


# Simple projectile class used by both player and enemies
class Bullet:
    bullet_size = 10
    bullet_speed = 10
    bullet_colour = (255, 255, 0)  # Yellow

    def __init__(self, x, y, direction, from_player=True):
        """Create a bullet at position (x, y) moving in direction"""
        self.rect = pygame.Rect(x, y, Bullet.bullet_size, Bullet.bullet_size)
        self.direction = direction  # (dx, dy) tuple
        self.speed = Bullet.bullet_speed
        self.from_player = from_player  # Track if bullet is from player or enemy

    def update(self):
        """Move the bullet"""
        self.rect.x += self.direction[0] * self.speed
        self.rect.y += self.direction[1] * self.speed

    def draw(self, screen, camera):
        """Draw the bullet on screen with camera offset"""
        bullet_screen_x = self.rect.x - camera.x
        bullet_screen_y = self.rect.y - camera.y
        pygame.draw.rect(screen, Bullet.bullet_colour, (bullet_screen_x, bullet_screen_y, Bullet.bullet_size, Bullet.bullet_size))

    def is_off_screen(self, map_width, map_height):
        """Check if bullet has gone outside the map"""
        return (self.rect.x < 0 or self.rect.x > map_width or 
                self.rect.y < 0 or self.rect.y > map_height)


# Health pack pickup that restores player health when collected
class HealthPack:
    pack_size = 15
    health_restore = 30  # restores 30 health per pack
    pack_colour = (0, 255, 0)  # Green

    def __init__(self, x, y):
        """Create a health pack at position (x, y)"""
        self.rect = pygame.Rect(x, y, HealthPack.pack_size, HealthPack.pack_size)

    def draw(self, screen, camera):
        """Draw the health pack on screen with camera offset"""
        pack_screen_x = self.rect.x - camera.x
        pack_screen_y = self.rect.y - camera.y
        pygame.draw.rect(screen, HealthPack.pack_colour, (pack_screen_x, pack_screen_y, HealthPack.pack_size, HealthPack.pack_size))


# Shotgun ammo pickup that grants 12 shotgun shots
class ShotgunPickup:
    pickup_size = 15
    ammo_per_pickup = 12  # gives 12 shots per pickup
    pickup_colour = (255, 100, 0)  # Orange

    def __init__(self, x, y):
        """Create a shotgun ammo pickup at position (x, y)"""
        self.rect = pygame.Rect(x, y, ShotgunPickup.pickup_size, ShotgunPickup.pickup_size)

    def draw(self, screen, camera):
        """Draw the shotgun pickup on screen with camera offset"""
        pickup_screen_x = self.rect.x - camera.x
        pickup_screen_y = self.rect.y - camera.y
        pygame.draw.rect(screen, ShotgunPickup.pickup_colour, (pickup_screen_x, pickup_screen_y, ShotgunPickup.pickup_size, ShotgunPickup.pickup_size))


class RiflePickup:
    pickup_size = 15
    ammo_per_pickup = 24  # 24 shots gives 8 bursts
    pickup_colour = (173, 216, 230)  # baby blue

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, RiflePickup.pickup_size, RiflePickup.pickup_size)

    def draw(self, screen, camera):
        pickup_screen_x = self.rect.x - camera.x
        pickup_screen_y = self.rect.y - camera.y
        pygame.draw.rect(screen, RiflePickup.pickup_colour, (pickup_screen_x, pickup_screen_y, RiflePickup.pickup_size, RiflePickup.pickup_size))


# Enemy unit subclass of Rect with basic AI for wandering and chasing player
class Enemy_Unit(pygame.Rect):
    enemy_size = 20
    enemy_speed = 2
    vision_range = 150  # 15 tiles * 20 pixels per tile
    enemy_colour = (255, 0, 0)

    def __init__(self, x, y, size, speed, walls, room_id=None):
        # initialize enemy as rect and setup AI state
        super().__init__(x, y, size, size)
        self.speed = speed
        self.rect = pygame.Rect(x, y, size, size)
        self.walls = walls
        self.room_id = room_id  # Track which room this enemy spawned in
        self.direction = random.choice([(1, 0),(-1, 0),(0, 1),(0, -1)])
        self.previous_direction = self.direction
        self.stuck_counter = 0
        self.stuck_threshold = 15
        self.player_spotted = False
        self.player_last_seen = None
        self.shoot_cooldown = 120

    def can_see_player(self, player):
        """Check if enemy can see the player (not blocked by walls, within range)"""
        # Check distance
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = (dx**2 + dy**2) ** 0.5
        
        if distance > Enemy_Unit.vision_range:
            return False
        
        # Check if line of sight is blocked by walls
        # Cast a ray from enemy to player and check for wall collisions
        # sample points along the path
        steps = int(distance / 5)  # Check every 5 pixels
        if steps < 1:
            steps = 1
            
        for step in range(steps + 1):
            t = step / max(steps, 1)
            check_x = self.rect.centerx + dx * t
            check_y = self.rect.centery + dy * t
            check_rect = pygame.Rect(check_x, check_y, 5, 5)
            
            # If any wall is hit before reaching player, vision is blocked
            if check_rect.collidelist(self.walls) != -1:
                return False
        
        return True

    def move(self, dx, dy):
        # move by dx/dy if no collision with walls
        new_rect = self.copy()
        new_rect.x += dx
        if new_rect.collidelist(self.walls) == -1:
            self.x += dx
        else:
            pass

        new_rect.y += dy
        if new_rect.collidelist(self.walls) == -1:
            self.y += dy
        else:
            pass

    def change_direction(self):
        # pick a new random direction that isn't directly back if possible
        possible_direction = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        possible_direction.remove((-self.previous_direction[0], -self.previous_direction[1]))

        valid_direction = []
        for dx, dy in possible_direction:
            test_rect = self.copy()
            test_rect.x = dx * self.speed
            test_rect.y = dy * self.speed

            if test_rect.collidelist(self.walls) == -1:
                valid_direction.append((dx, dy))

        if self.direction in valid_direction:
            self.stuck_counter = 0
            return

        if valid_direction:
            self.direction = random.choice(valid_direction)
            self.stuck_counter = 0
        else:
            self.stuck_counter += 1
            if self.stuck_counter > self.stuck_threshold:
                if len(possible_direction) > 1:
                    self.direction = random.choice(possible_direction)
                else:
                    self.direction = (-self.previous_direction[0], self.previous_direction[1])
                self.stuck_counter = 0

        self.previous_direction = self.direction

    def update(self, player, walls):
        """Update enemy AI"""
        # decrement shooting cooldown and refresh wall reference
        self.shoot_cooldown = max(0, self.shoot_cooldown - 1)
        self.walls = walls  # Update walls reference for current room
        
        # Check if can see player
        if self.can_see_player(player):
            self.player_spotted = True
            self.player_last_seen = (player.rect.centerx, player.rect.centery)
        
        # If player spotted, move toward last seen position
        if self.player_spotted and self.player_last_seen:
            dx = self.player_last_seen[0] - self.rect.centerx
            dy = self.player_last_seen[1] - self.rect.centery
            
            # Normalize direction
            distance = (dx**2 + dy**2) ** 0.5
            if distance > 0:
                dx_norm = dx / distance
                dy_norm = dy / distance
                
                # Move toward player
                self.move(dx_norm * self.speed, dy_norm * self.speed)
        else:
            # Wander aimlessly
            self.change_direction()
            self.move(self.direction[0] * self.speed, self.direction[1] * self.speed)


# Shotgun enemy variant that uses shotgun attack pattern
class ShotgunEnemy(Enemy_Unit):
    enemy_size = 20
    enemy_speed = 1.5  # slightly slower than rifle enemies
    enemy_colour = (200, 50, 0)  # Darker red/orange
    vision_range = 150

    def __init__(self, x, y, size, speed, walls, room_id=None):
        # initialize shotgun enemy with same base as Enemy_Unit
        super().__init__(x, y, size, speed, walls, room_id)
        self.shoot_cooldown = 200  # longer cooldown between shotgun blasts


class RifleEnemy(Enemy_Unit):
    enemy_size = 20
    enemy_speed = 2
    enemy_colour = (100, 149, 237)  # cornflower blue
    vision_range = 150

    def __init__(self, x, y, size, speed, walls, room_id=None):
        super().__init__(x, y, size, speed, walls, room_id)
        self.shoot_cooldown = 120  # same as regular but will burst in logic
        # burst state for spaced firing
        self.burst_remaining = 0
        self.burst_interval = 3  # frames between burst shots
        self.burst_timer = 0
        self.burst_direction = (0, 0)

# Simple world metadata class for grid sizing based on room count
class World:
    def __init__(self, room_width, room_height, target_room_count):
        self.room_width = room_width
        self.room_height = room_height
        self.target_room_count = target_room_count

        #calculate grid deimension based on target room count and approximate "field" shape
        self.grid_width = int((target_room_count ** 0.5) * 1.5)
        self.grid_height = int(target_room_count ** 0.5)

        # ensure grid dimensions can accommodate the desired number of rooms
        while self.grid_width * self.grid_height < target_room_count:
            self.grid_width += 1

        #print(f"World grid Dimensions: {self.grid_width} x {self.grid_height}")

# Map handles room templates, procedural generation, and object placement
class Map:
    room_data_list = [
        [  #Spawn Room (index 0)
            "XXXXXX  XXXXX",
            "X           X",
            "X           X",
            "      S      ",
            "             ",
            "X           X",
            "X           X",
            "XXXXXX  XXXXX",
        ],
        [#Room 0 (index 1)
            "XXXXXX  XXXXX",
            "X E         X",
            "X           X",
            "             ",
            "             ",
            "X   E   E   X",
            "X    E E    X",
            "XXXXXX  XXXXX",
        ],
        [ #Room 1 (index 2)
            "XXXXX   XXXXX",
            "X E         X",
            "X  X         ",
            "X            ",
            "XXXX     XXXX",
            "        EX  X",
            "         X  X",
            "X    E E    X",
            "XXXXXXXX  XXX",
         ],
        [ #Room 2 (index 3)
            "XXXXX   XXXXX",
            "X EXX   XX  X",
            "X  XX   XX  X",
            "   XX   XX   ",
            "   XX   XX   ",
            "X       XXE X",
            "X  XXE E    X",
            "XXXXXXXX  XXX",
        ],
        [ #Room 3  (index 4)
            "XXXX  XXXXXXX",
            "X E  XXX    X",
            "     XXX    X",
            "            X",
            "X    XXXE    ",
            "X    XX      ",
            "X    XX  E  X",
            "X   XXXXXXXXX",
        ],
        [ #Room 4  (index 5)
            "XX   XXXXXXXX",
            "X E  XXX    X",
            "X    XXX    X",
            "XXX       XXX",
            "XXX     E XXX",
            "     E E     ",
            "     E E     ",
            "XXXXX   XXXXX",
        ],
        [ #Room 5 (index 6)
            "XXXXX  XXXXXX",
            "X   E       X",
            "X  XXXXXXX  X",
            "   X     X   ",
            "   X     X   ",
            "X  XX   XX  X",
            "X           X",
            "XXXXXX  XXXXX",
        ],
        [ #Room 6 (index 7)
            "XXXXX   XXXXX",
            "X     E     X",
            "X  XX   XX  X",
            "   X  E  X   ",
            "   X     X   ",
            "X  XXXXXXX  X",
            "X     E     X",
            "XXXXX  XXXXXX",
        ],
        [  #Room 7 (index 8)
            "XXXXX   XXXXX",
            "X E         X",
            "X   XXXXX    ",
            "X      E     ",
            "XXX       XXX",
            "X   XXXXX   X",
            "     E E    X",
            "    E       X",
            "XXXXXXX  XXXX",
        ],
        [  # Exit Room (index 9)
            "XXXXXX  XXXXX",
            "X B  X  X B X",
            "X    X  X   X",
            "             ",
            "             ",
            "X    X  X   X",
            "X B  X  X B X",
            "XXXXXX  XXXXX",
        ],
    ]
    def __init__(self, room_data_list, spawn_room_index, grid_width, grid_height, room_size, num_rooms_before_exit=12, num_collectibles=0, collectible_size=20, key_size=20):
        """
        Initialize the Map Object.

        Args:
        :param room_data_list (List): a list of room data
        :param spawn_room_index (int): the index of the spawn room
        :param grid_width(int): the width of the map grid
        :param grid_height(int): the height of the map grid
        :param room_size(int): the size of each room tile in a pixel
        :param num_rooms_before_exit(int, optional): number of rooms before exit. Default to 12
        :param num_collectibles (int, optional):  Number of collectible in a room. Defaults to 0
        :param collectible_size (int, optional): Size of collectible. defaults to 20
        :param key_size (int optional): Size of the key. Defaults to 20
        """
        self.room_data_list = room_data_list
        self.spawn_room_index = spawn_room_index
        self.room_index = spawn_room_index
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.room_size = room_size
        
        # Calculate room dimensions from room data
        self.room_width = len(room_data_list[0][0]) * room_size  # width in pixels
        self.room_height = len(room_data_list[0]) * room_size    # height in pixels
        
        # Calculate total map dimensions
        self.map_width = self.grid_width * self.room_width
        self.map_height = self.grid_height * self.room_height
        self.walls = []
        self.start_pos = None
        self.exit = None
        self.num_collectibles = num_collectibles
        self.collectible_size = collectible_size
        self.key_size = key_size
        self.key = None
        self.enemy_spawn_points = []
        self.num_rooms_before_exit = num_rooms_before_exit
        self.current_room_count = 0
        self.exit_room_index = 9
        self.grid = [[None for _ in range(self.grid_width)] for _ in range(self.grid_height)] #2d array of None values
        self.room_counter = 0
        self.connection_graph = {} # initialize connection graph
        self.world_border_colour = (200, 200, 0)
        self.current_room = None  # Track current room loaded
        self.room_enemy_data = {}  # Store enemy spawn points for each room
        self.room_index_grid = {}  # Track which room template index is at each grid position
        self.generate_map() #generate the map
        self.generate_exit_room()
        # Initialize start position and enemies from spawn room
        self.start_pos = None
        self.exit = None
        self.enemy_spawn_points = []
        spawn_room = self.room_data_list[0]
        for y, row in enumerate(spawn_room):
            for x, col in enumerate(row):
                if col == "S":
                    self.start_pos = (x * 20, y * 20)
                elif col == "E":
                    self.enemy_spawn_points.append((x * 20, y * 20, 20, 20))
        
        # Load initial enemies for spawn room
        self.load_room_data(0, 0, 0)
        
        # Extract enemy spawn points for all room templates
        for idx, room_data in enumerate(self.room_data_list):
            room_enemies = []
            for y, row in enumerate(room_data):
                for x, col in enumerate(row):
                    if col == "E":
                        room_enemies.append((x * 20, y * 20, 20, 20))
            self.room_enemy_data[idx] = room_enemies
        
        self.generate_game_objects()

    def load_room_data(self, room_index, grid_x=None, grid_y=None):
        """Load walls and entities for a specific room at grid position"""
        if 0 <= room_index < len(self.room_data_list):
            # Calculate world position of this room
            room_x = grid_x * self.room_width if grid_x is not None else 0
            room_y = grid_y * self.room_height if grid_y is not None else 0
            
            # Extract enemy spawn points from the room template at this world position
            room_template = self.room_data_list[room_index]
            self.enemy_spawn_points = []
            for y, row in enumerate(room_template):
                for x, col in enumerate(row):
                    if col == "E":
                        # Offset relative coordinates by room's world position
                        world_x = room_x + x * 20
                        world_y = room_y + y * 20
                        self.enemy_spawn_points.append((world_x, world_y, 20, 20))
            #TODO: Add breach charge
            #TODO: Add Health Packs
            #TODO: Add Armor Packs

    def load(self):
        # rebuild map data structures from current room index and templates
        print("Loading Map....")
        self.spawn_room = self.room_data_list[0]
        self.exit_room = self.room_data_list[9]
        self.other_rooms = self.room_data_list[1:8]

        print("Spawn room:", self.spawn_room)
        print("Exit Room:", self.exit_room)
        print("Other Rooms:", self.other_rooms)

        self.walls = []
        self.start_pos = None
        self.exit = None

        #checks index and converts the letters in the respective items
        if 0 <= self.room_index <len(self.room_data_list):
            room_data = self.room_data_list[self.room_index]
            for y, row in enumerate(room_data):
                for x, col in enumerate(row):
                    if col == "X":
                        self.walls.append(pygame.Rect(x * 20, y * 20, 20, 20))
                    elif col == "S":
                        self.start_pos = (x * 20, y * 20)
                    elif col == "B":
                        self.exit = (x * 20, y * 20)
                        print("Found exit position in room")
                    elif col == "E":
                        self.enemy_spawn_points.append((x * 20, y * 20, 20, 20))

            if self.room_index == self.spawn_room_index and self.start_pos is None:
                raise ValueError("Spawn Room must have a start ('S') position")
            if self.room_index == self.exit_room_index and self.exit is None:
                raise ValueError("Exit room must have a exit ('B') position")
        else:
            raise IndexError("Room index out of Range")

#   ----- Map Generation Functions -----

    def generate_map(self):
        self.walls = [] #clears existing walls
        self.connection_graph = {} # clear connection graph
        self.room_counter = 0 #reset room counter
        self.room_index_grid = {}  # Reset room index tracking

        # Always place spawn room at (0, 0)
        spawn_template = self.room_data_list[0]
        self.place_room(spawn_template, 0, 0, 0, 0, room_index=0)
        self.room_counter = 1

        for y in range(self.grid_height):
            for x in range(self.grid_width):
                # Skip if it's the spawn room location
                if x == 0 and y == 0:
                    continue
                if random.random() < 0.4: #40% chance to place a room (increased from 20%)
                    #print(f"Placing room at ({x}, {y})")
                    room_index = random.randint(1, len(self.room_data_list) - 1)  # Exclude spawn room and exit room
                    room_template = self.room_data_list[room_index]
                    room_x = x * self.room_width
                    room_y =  y * self.room_height
                    self.place_room(room_template, room_x, room_y, x, y, room_index=room_index)
                    self.room_counter += 1
        
        # Add boundary walls around the entire map
        boundary_thickness = 20
        for x in range(0, self.map_width, boundary_thickness):
            # Top boundary
            self.walls.append(pygame.Rect(x, -boundary_thickness, boundary_thickness, boundary_thickness))
            # Bottom boundary
            self.walls.append(pygame.Rect(x, self.map_height, boundary_thickness, boundary_thickness))
        for y in range(0, self.map_height, boundary_thickness):
            # Left boundary
            self.walls.append(pygame.Rect(-boundary_thickness, y, boundary_thickness, boundary_thickness))
            # Right boundary
            self.walls.append(pygame.Rect(self.map_width, y, boundary_thickness, boundary_thickness))
        
        # Place exit room at bottom-right corner (always there, but locked until requirements met)
        max_x = self.grid_width - 1
        max_y = self.grid_height - 1
        exit_x = max_x * self.room_width
        exit_y = max_y * self.room_height
        exit_template = self.room_data_list[9]  # Exit room template
        self.place_room(exit_template, exit_x, exit_y, max_x, max_y, room_index=9)
        self.room_index_grid[(max_x, max_y)] = 9

    def place_room(self, room_template, x, y, grid_x, grid_y, room_index=None):
        for row_index, row in enumerate(room_template):
            for col_index, col in enumerate(row):
                if col == "X":
                    self.walls.append(pygame.Rect(x + col_index * 20, y + row_index * 20, 20, 20))
        
        self.grid[grid_y][grid_x] = room_template  # populate the grid
        if room_index is not None:
            self.room_index_grid[(grid_x, grid_y)] = room_index
            #print(f"grid_y: {grid_y}, grid_x: {grid_x}, grid_height: {self.grid_height}, grid_width: {self.grid_width}")
            # Identify entrance points (Will be added)

    def find_entrance_point(self, room_pos):
        #Basic: find the cent of the first open space
        x, y = room_pos
        room_template = self.grid[y // self.room_height][x // self.room_width]
        if room_template is None:
            return None #exit early if room_template is None

        for row_index, row in enumerate(room_template):
            for col_index, col in enumerate(row):
                if col == " ":
                    return (x + col_index * 20 + 10, y + row_index * 20 + 10)
        return None

    def place_exit_room(self):
        exit_x = (self.grid_width - 1) * self.room_width
        exit_y = (self.grid_height - 1) * self.room_height
        exit_template = self.room_data_list[9]
        self.place_room(exit_template, exit_x, exit_y, self.grid_width - 1, self.grid_height - 1)
        print(f"Placed exit room at ({self.grid_width - 1}, {self.grid_height -1}")

    def generate_exit_room(self):
        if self.current_room_count >= self.num_rooms_before_exit:
            self.exit_room_index = 9 #whatever the index for the exit room is
        else:
            self.exit_room_index = random.randint(0, len(self.room_data_list) -2)

    def generate_game_objects(self):
        self.collectibles = self.generate_collectibles(self.room_data_list[self.room_index], self.num_collectibles, self.collectible_size)
        self.key = self.generate_key(self.room_data_list[self.room_index], self.key_size)


    def generate_collectibles(self, room_data, num_collectibles, collectible_size):
        collectibles = []
        collectible_count = 0
        for y, row in enumerate(room_data):
            for x, col in enumerate(row):
                if col == "C" and collectible_count < num_collectibles:
                    collectibles.append(pygame.Rect(x * 20, y * 20, collectible_size, collectible_size))
                    collectible_count += 1
        return collectibles

    def generate_key(self, room_data, key_size):
        for y, row in enumerate(room_data):
            for x, col in enumerate(row):
                if col == "K":
                    return pygame.Rect(x * 20, y * 20, key_size, key_size)
        return None #return if no key found


#   ----- Draw Function -----

    def draw(self, screen, wall_colour, offset_x=0, offset_y=0):
        #Draw Walls
        for wall in self.walls:
            pygame.draw.rect(screen, wall_colour, wall.move(offset_x, offset_y))
        #Draw Collectibles
        for collectible in self.collectibles:
            pygame.draw.rect(screen, (0, 255, 0), collectible.move(offset_x, offset_y))
        #Draw Key
        if self.key:
            pygame.draw.rect(screen, (255, 255, 0), self.key.move(offset_x, offset_y))

        #draw the world border
        world_rect = pygame.Rect(
            offset_x,
            offset_y,
            self.grid_width * self.room_width,
            self.grid_height * self.room_height,
        )
        pygame.draw.rect(screen, self.world_border_colour, world_rect, 5) #5 = Border width

class Camera:
    def __init__(self, width, height, map_width, map_height):
        self.width = width
        self.height = height
        self.map_width = map_width
        self.map_height = map_height
        self.x = 0
        self.y = 0

    def update(self, target):
        """Center the camera on the target (Player) and clamp to map boundaries"""
        # Center camera on player
        self.x = target.rect.centerx - self.width // 2
        self.y = target.rect.centery - self.height // 2
        
        # Clamp camera to map boundaries
        self.x = max(0, min(self.x, self.map_width - self.width))
        self.y = max(0, min(self.y, self.map_height - self.height))

class Game:
    def __init__(self, screen_width, screen_height):
        room_size = 20
        self.world = World(100, 100, 40)
        self.map = Map(
            Map.room_data_list,
            0,
            grid_width = self.world.grid_width,
            grid_height = self.world.grid_height,
            room_size=room_size
        )
        pygame.init()
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        self.clock = pygame.time.Clock()
        self.running = True
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.player = Player(self.map.start_pos[0], self.map.start_pos[1], self.map.walls)
        self.camera = Camera(screen_width, screen_height, self.map.map_width, self.map.map_height)
        self.enemies = []
        self.bullets = []
        self.health_packs = []  # list of HealthPack objects
        self.ammo_pickups = []  # list of weapon ammo pickups (ShotgunPickup/RiflePickup)
        self.cleared_rooms = set()  # Track which rooms have been cleared
        self.rooms_entered_with_enemies = set()  # Track rooms that had enemies when entered
        self.all_rooms_cleared = False  # Track if all rooms have been cleared
        self.exit_available = False  # Track if exit is accessible (10+ rooms cleared)
        self.exit_spawned = False  # Track if exit room has been spawned
        self.current_room_id = None  # Track current room to detect transitions
        self.game_over = False  # Track if player is dead
        self.font = pygame.font.Font(None, 24)
        self.smallfont = pygame.font.Font(None, 15)
        self.largefont = pygame.font.Font(None, 30)        
        self.rooms_entered_with_enemies = set()  # Track rooms that had enemies when entered

        # print(f"Map size: {self.map.map_width}x{self.map.map_height}")
        # print(f"Room size: {self.map.room_width}x{self.map.room_height}")
        # print(f"Player start: {self.map.start_pos}")
        self.spawn_enemies()


    def run(self):
        while self.running:
            self.events()
            self.update()
            self.draw()
            self.clock.tick(60)

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if self.game_over:
                    # Only allow R to restart when dead
                    if event.key == pygame.K_r:
                        self.reset_game()
                else:
                    # Normal game controls
                    if event.key == pygame.K_SPACE:
                        # Fire current weapon
                        weapon = self.player.get_current_weapon()
                        if weapon.can_fire():
                            bullets = weapon.fire(
                                (self.player.rect.centerx, self.player.rect.centery),
                                self.player.facing_direction
                            )
                            self.bullets.extend(bullets)
                    elif event.key == pygame.K_x:
                        # Cycle weapon
                        self.player.cycle_weapon()

    def spawn_enemies(self, room_id=None):
        """Spawn enemies at enemy spawn points in the current room, add to existing list instead of replacing"""
        for spawn_x, spawn_y, size, _ in self.map.enemy_spawn_points:
            r = random.random()
            if r < 0.1:
                # 10% chance shotgun enemy
                enemy = ShotgunEnemy(spawn_x, spawn_y, size, 1.5, self.map.walls, room_id=room_id)
                print("Spawned ShotgunEnemy")
            elif r < 0.3:
                # 20% chance rifle enemy (between 0.1 and 0.3)
                enemy = RifleEnemy(spawn_x, spawn_y, size, 2, self.map.walls, room_id=room_id)
                print("Spawned RifleEnemy")
            else:
                # remaining 70% basic enemy
                enemy = Enemy_Unit(spawn_x, spawn_y, size, 2, self.map.walls, room_id=room_id)
                print("Spawned basic Enemy_Unit")
            self.enemies.append(enemy)
        #print(f"Spawned {len(self.enemies)} enemies")


    def check_if_all_cleared(self):
        """Check if minimum rooms (10) have been cleared, then mark exit as available"""
        # Mark exit as available after clearing at least 10 rooms
        if len(self.cleared_rooms) >= 10 and not self.exit_available:
            self.exit_available = True
            print(f"Minimum rooms cleared! Cleared: {len(self.cleared_rooms)} rooms - EXIT AVAILABLE")

    def check_exit_reached(self):
        """Check if player has reached the exit room and victory conditions are met"""
        # Exit room is at bottom-right corner
        max_x = self.map.grid_width - 1
        max_y = self.map.grid_height - 1
        grid_x, grid_y = self.get_current_room()
        
        # Check if player is in exit room and exit is available
        if grid_x == max_x and grid_y == max_y and self.exit_available:
            print("Victory! Resetting game...")
            self.reset_game()

    def reset_game(self):
        """Reset the game to a fresh state with a new map"""
        # Clear all game state
        self.enemies.clear()
        self.bullets.clear()
        self.health_packs.clear()
        self.ammo_pickups.clear()
        self.cleared_rooms.clear()
        self.rooms_entered_with_enemies.clear()
        self.exit_available = False
        self.game_over = False  # Clear death state
        self.current_room_id = None
        
        # Generate a new map
        self.map = Map(
            Map.room_data_list,
            0,
            grid_width=self.world.grid_width,
            grid_height=self.world.grid_height,
            room_size=20
        )
        
        # Reset player to new spawn position with full health
        self.player = Player(self.map.start_pos[0], self.map.start_pos[1], self.map.walls)
        self.camera = Camera(self.screen_width, self.screen_height, self.map.map_width, self.map.map_height)
        
        # Spawn enemies for the new game
        self.spawn_enemies()


    def get_current_room(self):
        """Determine which room the player is currently in"""
        # compute grid coordinates from player position
        room_width = self.map.room_width
        room_height = self.map.room_height
        grid_x = self.player.rect.x // room_width
        grid_y = self.player.rect.y // room_height
        
        # Clamp to grid boundaries
        grid_x = max(0, min(grid_x, self.map.grid_width - 1))
        grid_y = max(0, min(grid_y, self.map.grid_height - 1))
        
        return grid_x, grid_y

    def check_room_transition(self):
        """Check if player has entered a new room and update map accordingly"""
        # find grid cell for player and load new room if changed
        grid_x, grid_y = self.get_current_room()
        #print(f"DEBUG: Player grid position ({grid_x}, {grid_y})")
        
        if grid_y < len(self.map.grid) and grid_x < len(self.map.grid[grid_y]):
            room = self.map.grid[grid_y][grid_x]
            room_id = (grid_x, grid_y)
            
            if room and room != self.map.current_room:
                print(f"Transitioning to new room at ({grid_x}, {grid_y})")
                #print(f"room_index_grid has {len(self.map.room_index_grid)} entries: {self.map.room_index_grid}")
                self.map.current_room = room
                
                # Get the room index from our tracking dict
                room_index = self.map.room_index_grid.get(room_id, None)
                #print(f"DEBUG: Looking up room_id={room_id}, room_index={room_index}")
                
                if room_index is not None:
                    #print(f"Loading room data index {room_index}")
                    self.map.load_room_data(room_index, grid_x, grid_y)
                    #print(f"DEBUG: room_enemy_data[{room_index}] = {self.map.room_enemy_data.get(room_index, [])}")
                    #print(f"DEBUG: After load_room_data, enemy_spawn_points={self.map.enemy_spawn_points}")
                else:
                    print(f"WARNING: No room_index found for {room_id}")
                    self.map.enemy_spawn_points = []
                
                # Only spawn enemies if room hasn't been cleared
                if room_id not in self.cleared_rooms:
                    # Count enemies already in this room
                    enemies_in_room = len([e for e in self.enemies if e.room_id == room_id])
                    # Only spawn if we haven't already spawned enemies for this room
                    if enemies_in_room == 0:
                        self.spawn_enemies(room_id=room_id)
                        # Track that this room has enemies
                        if len([e for e in self.enemies if e.room_id == room_id]) > 0:
                            self.rooms_entered_with_enemies.add(room_id)
                        #print(f"DEBUG: Spawned enemies for room {room_id}")
                    #else:
                        #print(f"DEBUG: Room {room_id} already has {enemies_in_room} enemies")
                
                self.current_room_id = room_id  # Update current room tracking
                
                # Spawn health packs randomly in new rooms (30% chance)
                if random.random() < 0.3:
                    # Pick a random open space in the room
                    room_template = self.map.grid[grid_y][grid_x]
                    if room_template:
                        for _ in range(random.randint(1, 2)):  # 1-2 packs per room
                            attempts = 0
                            while attempts < 10:
                                rand_x = random.randint(0, len(room_template[0]) - 1)
                                rand_y = random.randint(0, len(room_template) - 1)
                                if room_template[rand_y][rand_x] == " ":  # Empty space
                                    world_x = grid_x * self.map.room_width + rand_x * 20
                                    world_y = grid_y * self.map.room_height + rand_y * 20
                                    self.health_packs.append(HealthPack(world_x, world_y))
                                    break
                                attempts += 1
                
                # Spawn shotgun ammo pickups randomly in new rooms (20% chance)
                if random.random() < 0.2:
                    room_template = self.map.grid[grid_y][grid_x]
                    if room_template:
                        for _ in range(random.randint(1, 1)):  # 1 shotgun pickup per room max
                            attempts = 0
                            while attempts < 10:
                                rand_x = random.randint(0, len(room_template[0]) - 1)
                                rand_y = random.randint(0, len(room_template) - 1)
                                if room_template[rand_y][rand_x] == " ":  # Empty space
                                    world_x = grid_x * self.map.room_width + rand_x * 20
                                    world_y = grid_y * self.map.room_height + rand_y * 20
                                    self.ammo_pickups.append(ShotgunPickup(world_x, world_y))
                                    break
                                attempts += 1
                # Spawn rifle ammo pickups randomly in new rooms (15% chance)
                if random.random() < 0.15:
                    room_template = self.map.grid[grid_y][grid_x]
                    if room_template:
                        for _ in range(random.randint(1, 1)):
                            attempts = 0
                            while attempts < 10:
                                rand_x = random.randint(0, len(room_template[0]) - 1)
                                rand_y = random.randint(0, len(room_template) - 1)
                                if room_template[rand_y][rand_x] == " ":
                                    world_x = grid_x * self.map.room_width + rand_x * 20
                                    world_y = grid_y * self.map.room_height + rand_y * 20
                                    self.ammo_pickups.append(RiflePickup(world_x, world_y))
                                    break
                                attempts += 1

    def update(self):
        # handle input, movement, bullets, enemies, and room clearing logic
        # Skip all game logic if player is dead
        if self.game_over:
            return
        
        # Check if player is dead
        if self.player.health <= 0:
            self.game_over = True
            print("Player died!")
            return
        
        keys = pygame.key.get_pressed()
        self.player.handle_imput(keys)

        # Apply the player's movement
        self.player.move(self.player.movement_x, self.player.movement_y)

        # Update weapon cooldowns and process any burst shots
        player_pos = (self.player.rect.centerx, self.player.rect.centery)
        player_dir = self.player.facing_direction
        new_bullets = []
        for weapon in self.player.weapons:
            bullets_from_weapon = weapon.update(player_pos, player_dir)
            if bullets_from_weapon:
                new_bullets.extend(bullets_from_weapon)
        # append any bullets generated by weapons (rifle bursts)
        self.bullets.extend(new_bullets)

        # Check if player entered a new room
        self.check_room_transition()

        # Update camera to follow player
        self.camera.update(self.player)
        # print(f"Player: ({self.player.rect.x}, {self.player.rect.y}) | Camera: ({self.camera.x}, {self.camera.y})")

        # Update bullets
        for bullet in self.bullets[:]:  # Use slice to iterate over copy
            bullet.update()
            # Remove bullet if it goes off screen
            if bullet.is_off_screen(self.map.map_width, self.map.map_height):
                self.bullets.remove(bullet)
                continue
            
            # Check collision with walls
            wall_idx = bullet.rect.collidelist(self.map.walls)
            if wall_idx != -1:
                # if a bullet hits a wall, destroy the wall and the bullet
                # currently all walls are destructible; you can add flags later
                del self.map.walls[wall_idx]
                if bullet in self.bullets:
                    self.bullets.remove(bullet)
                continue
            
            # Check collision with enemies (only player bullets hurt enemies)
            for enemy in self.enemies[:]:
                if bullet.rect.colliderect(enemy) and bullet.from_player:
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    self.enemies.remove(enemy)
                    break
            
            # Check collision with player (only enemy bullets hurt player)
            if bullet.rect.colliderect(self.player) and not bullet.from_player:
                if bullet in self.bullets:
                    self.bullets.remove(bullet)
                self.player.take_damage(10)  # enemy bullets deal 10 damage
                print(f"Player hit! Health: {self.player.health}/{self.player.max_health}")

        # Check health pack pickups
        for pack in self.health_packs[:]:
            if self.player.rect.colliderect(pack.rect):
                self.player.heal(HealthPack.health_restore)
                self.health_packs.remove(pack)
                print(f"Health pack picked up! Health: {self.player.health}/{self.player.max_health}")

        # Check weapon ammo pickups
        for pickup in self.ammo_pickups[:]:
            if self.player.rect.colliderect(pickup.rect):
                if isinstance(pickup, ShotgunPickup):
                    self.player.shotgun.ammo += ShotgunPickup.ammo_per_pickup
                    print(f"Shotgun ammo picked up! Ammo: {self.player.shotgun.ammo}")
                elif isinstance(pickup, RiflePickup):
                    self.player.rifle.ammo += RiflePickup.ammo_per_pickup
                    print(f"Rifle ammo picked up! Ammo: {self.player.rifle.ammo}")
                self.ammo_pickups.remove(pickup)

        # Update enemy positions and logic
        for enemy in self.enemies[:]:
            enemy.update(self.player, self.map.walls)
            
            # Enemy shooting logic (only if enemy is still alive)
            if enemy in self.enemies and enemy.player_spotted and enemy.shoot_cooldown <= 0:
                # Enemy firing patterns vary by type
                if isinstance(enemy, ShotgunEnemy):
                    # Shotgun blast towards player
                    dx = self.player.rect.centerx - enemy.centerx
                    dy = self.player.rect.centery - enemy.centery
                    distance = (dx**2 + dy**2) ** 0.5
                    
                    if distance > 0:
                        # Fire 4-5 bullets in a cone
                        base_angle = math.atan2(dy, dx)
                        spread_angle = 40  # smaller spread than player shotgun
                        num_bullets = random.randint(4, 5)
                        
                        for i in range(num_bullets):
                            angle_offset = (spread_angle / (num_bullets - 1)) * (i - (num_bullets - 1) / 2) * (math.pi / 180)
                            angle = base_angle + angle_offset
                            direction = (math.cos(angle), math.sin(angle))
                            bullet = Bullet(enemy.centerx, enemy.centery, direction, from_player=False)
                            self.bullets.append(bullet)
                        enemy.shoot_cooldown = 200  # longer cooldown for shotgun
                elif isinstance(enemy, RifleEnemy):
                    # Rifle enemies fire a three‑round burst with spaced shots
                    # First, if a burst is already in progress, handle it
                    if enemy.burst_remaining > 0:
                        # countdown until next shot
                        enemy.burst_timer -= 1
                        if enemy.burst_timer <= 0:
                            # fire one bullet in stored direction
                            bullet = Bullet(enemy.centerx, enemy.centery, enemy.burst_direction, from_player=False)
                            self.bullets.append(bullet)
                            enemy.burst_remaining -= 1
                            enemy.burst_timer = enemy.burst_interval
                    # if not currently bursting, maybe start one
                    elif enemy.player_spotted and enemy.shoot_cooldown <= 0:
                        dx = self.player.rect.centerx - enemy.centerx
                        dy = self.player.rect.centery - enemy.centery
                        distance = (dx**2 + dy**2) ** 0.5
                        if distance > 0:
                            direction = (dx / distance, dy / distance)
                            # fire first bullet immediately
                            bullet = Bullet(enemy.centerx, enemy.centery, direction, from_player=False)
                            self.bullets.append(bullet)
                            # schedule remaining two
                            enemy.burst_remaining = 2
                            enemy.burst_timer = enemy.burst_interval
                            enemy.burst_direction = direction
                            enemy.shoot_cooldown = 120  # reset cooldown as before
                else:
                    # Regular enemy (basic red) shoots single bullet
                    dx = self.player.rect.centerx - enemy.centerx
                    dy = self.player.rect.centery - enemy.centery
                    distance = (dx**2 + dy**2) ** 0.5
                    
                    if distance > 0:
                        direction = (dx / distance, dy / distance)
                        bullet = Bullet(enemy.centerx, enemy.centery, direction, from_player=False)
                        self.bullets.append(bullet)
                        enemy.shoot_cooldown = 120  # Cooldown before next shot
        
        # Check if current room is cleared of enemies
        grid_x, grid_y = self.get_current_room()
        room_id = (grid_x, grid_y)
        # Count enemies still in this room
        enemies_in_current_room = len([e for e in self.enemies if e.room_id == room_id])
        # Only mark as cleared if: room had enemies initially AND all enemies from this room are dead
        if (enemies_in_current_room == 0 and 
            room_id not in self.cleared_rooms and 
            room_id in self.rooms_entered_with_enemies and 
            self.map.current_room is not None):
            self.cleared_rooms.add(room_id)
            print(f"Room {room_id} cleared! ({len(self.cleared_rooms)}/{len(self.rooms_entered_with_enemies)})")
            self.check_if_all_cleared()
        
        # Check if player has reached the exit
        self.check_exit_reached()

    def draw(self):
        self.screen.fill((0, 0, 0))

        # Draw the map (Walls, rooms) - offset by camera
        offset_x = -self.camera.x
        offset_y = -self.camera.y
        self.map.draw(self.screen, (120, 115, 128), offset_x, offset_y)

        # Draw the player
        player_screen_x = self.player.rect.x - self.camera.x
        player_screen_y = self.player.rect.y - self.camera.y
        pygame.draw.rect(self.screen, Player.player_colour, (player_screen_x, player_screen_y, Player.player_size, Player.player_size))

        # Draw enemies
        for enemy in self.enemies:
            enemy_screen_x = enemy.x - self.camera.x
            enemy_screen_y = enemy.y - self.camera.y
            # different colours per subclass
            if isinstance(enemy, ShotgunEnemy):
                colour = ShotgunEnemy.enemy_colour
            elif isinstance(enemy, RifleEnemy):
                colour = RifleEnemy.enemy_colour
            else:
                colour = Enemy_Unit.enemy_colour  # basic red
            pygame.draw.rect(self.screen, colour, (enemy_screen_x, enemy_screen_y, enemy.width, enemy.height))

        # Draw health packs
        for pack in self.health_packs:
            pack.draw(self.screen, self.camera)

        # Draw ammo pickups (both shotgun and rifle)
        for pickup in self.ammo_pickups:
            pickup.draw(self.screen, self.camera)

        # Draw bullets
        for bullet in self.bullets:
            bullet.draw(self.screen, self.camera)

        # Draw healthbar (top-left corner)
        healthbar_width = 200
        healthbar_height = 20
        healthbar_x = 10
        healthbar_y = 10
        health_ratio = max(0, self.player.health / self.player.max_health)  # Clamp to 0-1
        
        # Background (red for empty)
        pygame.draw.rect(self.screen, (255, 0, 0), (healthbar_x, healthbar_y, healthbar_width, healthbar_height))
        # Foreground (green for filled)
        pygame.draw.rect(self.screen, (0, 255, 0), (healthbar_x, healthbar_y, healthbar_width * health_ratio, healthbar_height))
        # Border
        pygame.draw.rect(self.screen, (255, 255, 255), (healthbar_x, healthbar_y, healthbar_width, healthbar_height), 2)
        
        # Health text
        health_text = self.font.render(f"Health: {int(self.player.health)}/{self.player.max_health}", True, (255, 255, 255))
        self.screen.blit(health_text, (healthbar_x + 5, healthbar_y + 25))
        
        # Display current weapon and ammo
        current_weapon = self.player.get_current_weapon()
        # colour: orange for shotgun, baby blue for rifle, yellow for pistol/basic
        if current_weapon.name == "Shotgun":
            weapon_colour = (255, 165, 0)
        elif current_weapon.name == "Rifle":
            weapon_colour = (173, 216, 230)
        else:
            weapon_colour = (255, 255, 0)
        weapon_text = self.font.render(
            f"{current_weapon.name}: {current_weapon.ammo} (Press X to cycle)", True, weapon_colour
        )
        weapon_text_rect = weapon_text.get_rect(topleft=(10, 60))
        self.screen.blit(weapon_text, weapon_text_rect)
        # Brief aim instructions
        aim_text = self.font.render("Aim with WASD (move with arrows)", True, (200, 200, 200))
        self.screen.blit(aim_text, (10, 80))
        
        # Display coordinates
        text = self.font.render(
            f"({self.player.rect.x}, {self.player.rect.y})", True, (255, 255, 255)
        )
        text_rect = text.get_rect(topright=(self.screen_width - 10, 10))
        self.screen.blit(text, text_rect)

        # Display enemy count
        enemy_text = self.font.render(
            f"Enemies: {len(self.enemies)}", True, (255, 255, 255)
        )
        enemy_text_rect = enemy_text.get_rect(topright=(self.screen_width - 10, 40))
        self.screen.blit(enemy_text, enemy_text_rect)

        # Display room progress
        total_rooms = len(self.map.room_index_grid)
        cleared_rooms = len(self.cleared_rooms)
        progress_text = self.font.render(
            f"Rooms: {cleared_rooms}/{total_rooms}", True, (255, 255, 255)
        )
        progress_text_rect = progress_text.get_rect(topright=(self.screen_width - 10, 70))
        self.screen.blit(progress_text, progress_text_rect)

        # Display exit ready message if requirements met
        if self.exit_available:
            exit_text = self.largefont.render(
                "EXIT READY!", True, (0, 255, 0)
            )
            exit_text_rect = exit_text.get_rect(center=(self.screen_width // 2, 30))
            self.screen.blit(exit_text, exit_text_rect)
        else:
            # Show how many more rooms needed
            rooms_needed = 10 - len(self.cleared_rooms)
            if rooms_needed > 0:
                requirement_text = self.font.render(
                    f"Clear {rooms_needed} more rooms to unlock exit", True, (255, 165, 0)
                )
                requirement_text_rect = requirement_text.get_rect(center=(self.screen_width // 2, 30))
                self.screen.blit(requirement_text, requirement_text_rect)

        # Draw game over screen if dead
        if self.game_over:
            # Semi-transparent overlay
            overlay = pygame.Surface((self.screen_width, self.screen_height))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))
            
            # YOU DIED text in red
            death_text = self.largefont.render("YOU DIED", True, (255, 0, 0))
            death_text_rect = death_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 60))
            self.screen.blit(death_text, death_text_rect)
            
            # Restart instructions
            restart_text = self.font.render("Press R to restart", True, (255, 255, 255))
            restart_text_rect = restart_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 20))
            self.screen.blit(restart_text, restart_text_rect)

        pygame.display.flip()

if __name__ == "__main__":
    game = Game(800, 600)
    game.run()
    pygame.quit()
