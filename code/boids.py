import pygame
from random import randint
import math
from support import get_distance, lerp1D

minute = 60 * 60  # 60fps * 60 seconds


class Flock:
    def __init__(self, surface, flock_size, use_predator=False, use_wind=False):
        self.surface = surface
        self.chunk_size = 80
        # each chunk is a list of boids (3dim array) (use + 1 in case rounding down neccessary)
        self.chunks = [[[] for x in range((self.surface.get_width() // self.chunk_size) + 1)]
                       for y in range((self.surface.get_height() // self.chunk_size) + 1)]

        self.boids = [Boid(self.surface) for b in range(flock_size)]

        self.use_predator = use_predator
        if self.use_predator:
            self.predator = BoidPredator(self.surface)
        else:
            self.predator = None

        self.max_wind = 3
        self.min_wind_change = int(minute * 0.1)
        self.max_wind_change = int(minute * 0.2)
        self.wind_transition = 60
        self.wind_change = randint(self.min_wind_change, self.max_wind_change)
        self.use_wind = use_wind
        self.wind = [0, 0]
        self.new_wind = [0.0, 0.0]  # wind for next transition

    def update(self):
        self.wind_change -= 1
        # lerp wind to new wind if in transitional period
        if -self.wind_transition <= self.wind_change < 0 and self.use_wind:
            self.wind[0] = lerp1D(self.wind[0], self.new_wind[0], abs(self.wind_change) / self.wind_transition)
            self.wind[1] = lerp1D(self.wind[1], self.new_wind[1], abs(self.wind_change) / self.wind_transition)
        # set new wind for next transition if transition is completed
        elif self.wind_change < -self.wind_transition and self.use_wind:
            self.new_wind[0] = randint(-self.max_wind * 100, self.max_wind * 100) / 100
            self.new_wind[1] = randint(-self.max_wind * 100, self.max_wind * 100) / 100
            self.wind_change = randint(self.min_wind_change, self.max_wind_change)

        # update predator
        if self.use_predator:
            self.predator.update(self.boids, self.wind)
        # update boids by chunk
        # first update chunks (reset first so empty)
        self.chunks = [[[] for x in range(self.surface.get_width() // self.chunk_size + 1)]
                       for y in range(self.surface.get_height() // self.chunk_size + 1)]
        for b in self.boids:
            pos = b.get_pos()
            # find boid chunk index
            y = int(pos[1] // self.chunk_size)
            x = int(pos[0] // self.chunk_size)
            print(y, x)
            self.chunks[y][x].append(b)

        # x, y
        neighbour_chunks = [[-1, -1], [0, -1], [1, -1],
                            [-1, 0],  [0, 0],  [1, 0],
                            [-1, 1],  [0, 1],  [1, 1]]
        for y in range(len(self.chunks)):
            for x in range(len(self.chunks[y])):
                # only do chunk checks for chunks that are not empty
                if len(self.chunks[y][x]) > 0:
                    # collect neighbouring boids for chunk
                    neighbours = []
                    for n in neighbour_chunks:
                        # ensure chunk is within range
                        if 0 <= y + n[1] < len(self.chunks) and 0 <= x + n[0] < len(self.chunks[0]):
                            ny = y + n[1]
                            nx = x + n[0]
                            neighbours += self.chunks[ny][nx]
                    # update boids in chunk using neighbour list
                    for b in self.chunks[y][x]:
                        # self.boids replace with neighbours
                        b.update(neighbours, self.wind, self.predator)

    def draw(self):
        for y in range(len(self.chunks)):
            pygame.draw.line(self.surface, "green", (0, y * self.chunk_size), (self.surface.get_width(), y * self.chunk_size), 1)
            for x in range(len(self.chunks[y])):
                pygame.draw.line(self.surface, "green", (x * self.chunk_size, 0), (x * self.chunk_size, self.surface.get_height()), 1)
        for b in self.boids:
            b.draw()
        if self.use_predator:
            self.predator.draw()


class Boid:
    def __init__(self, surface):
        self.surface = surface
        self.rot_deg = 0

        self.pos = [randint(0, surface.get_width()), randint(0, surface.get_height())]  # x, y
        self.vel = [0, 0]  # x, y
        self.min_speed = 1
        self.max_speed = 5  # 3 or 5

        self.protected_r = 10  # protected distance to steer away from other boids
        self.visual_r = 80  # 50 distance boid can see other boids  MUST BE LESS THAN CHUNK SIZE

        self.turn_factor = 0.1   # 0.1 or 0.05 amount boid turns (multiplier)
        self.screen_margin = 500  # 200 margin from screen edge before turning

        self.matching_factor = 0.02  # loose 0.02 or 0.05 tight, tend towards average velocity (multiplier)
        self.centering_factor = 0.001  # 0.005 tend towards center of visual flock (multiplier)
        self.escape_factor = 0.2  # factor boids attempt to escape predator (multiplier)

    def get_pos(self):
        return self.pos

    def get_vel(self):
        return self.vel

    def update(self, boids, wind, predator=None):
        # steering
        close_dx = 0
        close_dy = 0
        # alignment and cohesion
        avg_x_pos = 0
        avg_y_pos = 0
        avg_x_vel = 0
        avg_y_vel = 0
        neighbours = 0

        # loop through all other boids in flock
        for b in boids:
            bpos = b.get_pos()
            bvel = b.get_vel()
            dist = get_distance(self.pos, bpos)
            # within protected
            if dist <= self.protected_r:
                close_dx += self.pos[0] - bpos[0]
                close_dy += self.pos[1] - bpos[1]
            # outside protected but within visual range
            elif dist <= self.visual_r:
                # accumulate averages and total neighbours
                neighbours += 1
                avg_x_pos += bpos[0]
                avg_y_pos += bpos[1]
                avg_x_vel += bvel[0]
                avg_y_vel += bvel[1]
                pygame.draw.line(self.surface, "pink", self.pos, bpos, 1)

        # - alignment and cohesion -
        if neighbours > 0:
            # calculate avgs
            avg_x_pos /= neighbours
            avg_y_pos /= neighbours
            avg_x_vel /= neighbours
            avg_y_vel /= neighbours
        # apply avg pos to vel
        self.vel[0] += (avg_x_pos - self.pos[0]) * self.centering_factor
        self.vel[1] += (avg_y_pos - self.pos[1]) * self.centering_factor
        # apply avg vels (difference between vels and multiply by match factor multiplier)
        self.vel[0] += (avg_x_vel - self.vel[0]) * self.matching_factor
        self.vel[1] += (avg_y_vel - self.vel[1]) * self.matching_factor

        # - steering away from other boids -
        self.vel[0] += close_dx * self.turn_factor
        self.vel[1] += close_dy * self.turn_factor

        # - steer away from predator -
        if predator is not None:
            pred_pos = predator.get_pos()
            if get_distance(self.pos, pred_pos) <= self.visual_r:
                self.vel[0] += (self.pos[0] - pred_pos[0]) * self.escape_factor
                self.vel[1] += (self.pos[1] - pred_pos[1]) * self.escape_factor

        # - steer away from screen edges -
        # left margin
        if self.pos[0] < self.screen_margin:
            self.vel[0] = self.vel[0] + self.turn_factor
        # right margin
        elif self.pos[0] > self.surface.get_width() - self.screen_margin:
            self.vel[0] = self.vel[0] - self.turn_factor
        # bottom margin
        if self.pos[1] > self.surface.get_height() - self.screen_margin:
            self.vel[1] = self.vel[1] - self.turn_factor
        # top margin
        elif self.pos[1] < self.screen_margin:
            self.vel[1] = self.vel[1] + self.turn_factor

        # - set speed within bounds -
        speed = math.sqrt(self.vel[0]**2 + self.vel[1]**2)
        # find fraction of speed each vel component makes up then multiply to cap at max or min speed
        if speed > self.max_speed:
            self.vel[0] = (self.vel[0] / speed) * self.max_speed
            self.vel[1] = (self.vel[1] / speed) * self.max_speed
        elif speed < self.min_speed:
            self.vel[0] = (self.vel[0] / speed) * self.min_speed
            self.vel[1] = (self.vel[1] / speed) * self.min_speed

        # - apply velocity and wind -
        # wind is separate force to boid velocity (external force)
        self.pos[0] += self.vel[0] + wind[0]
        self.pos[1] += self.vel[1] + wind[1]

        # - calculate angle (for rendering) -
        self.rot_deg = math.degrees(math.atan2(self.vel[0], self.vel[1]))

    def draw(self):
        point_ahead = 6
        point_sides = 2
        outline = [
            # point ahead
            [self.pos[0] + math.sin(math.radians(self.rot_deg)) * point_ahead,
             self.pos[1] + math.cos(math.radians(self.rot_deg)) * point_ahead],
            # point side1
            [self.pos[0] + math.sin(math.radians(self.rot_deg + 90)) * point_sides,
             self.pos[1] + math.cos(math.radians(self.rot_deg + 90)) * point_sides],
            # point side2
            [self.pos[0] + math.sin(math.radians(self.rot_deg - 90)) * point_sides,
             self.pos[1] + math.cos(math.radians(self.rot_deg - 90)) * point_sides]
        ]
        pygame.draw.polygon(self.surface, "red", outline)


class BoidPredator:
    def __init__(self, surface):
        self.surface = surface
        self.rot_deg = 0

        self.pos = [randint(0, surface.get_width()), randint(0, surface.get_height())]  # x, y
        self.vel = [0, 0]  # x, y
        self.min_speed = 1
        self.max_speed = 7  # 3 or 5

        self.turn_factor = 0.1  # 0.1 or 0.05 amount boid turns (multiplier)
        self.screen_margin = 400  # 200 margin from screen edge before turning

        self.min_attack_timer = int(minute * 0.1)
        self.max_attack_timer = int(minute * 0.7)
        self.attack_timer = randint(self.min_attack_timer, self.max_attack_timer)
        self.attack_duration = 60 * 5  # 60fps * 5 seconds

        self.centering_factor = 0.01  # how fast moves towards flock center (multiplier)
        self.circling_pos = [randint(0, self.surface.get_width()), randint(0, self.surface.get_height())]
        self.circling_factor = 0.004
        self.circling_max_speed = 4

    def get_pos(self):
        return self.pos

    def update(self, boids, wind):
        # alignment and cohesion
        avg_x_pos = 0
        avg_y_pos = 0
        neighbours = 0

        self.attack_timer -= 1

        # loop through all other boids in flock
        for b in boids:
            bpos = b.get_pos()
            dist = get_distance(self.pos, bpos)
            # attack if timer is in attack window
            if -self.attack_duration <= self.attack_timer < 0:
                avg_x_pos += bpos[0]
                avg_y_pos += bpos[1]
                neighbours += 1

        # if attack timer is exceeded, reset all
        if self.attack_timer < -self.attack_duration:
            self.attack_timer = randint(self.min_attack_timer, self.max_attack_timer)
            self.circling_pos = [randint(0, self.surface.get_width()), randint(0, self.surface.get_height())]

        # tend towards avg pos of entire flock when attacking (neighbours only incremented when attacking)
        if neighbours > 0:
            avg_x_pos /= neighbours
            avg_y_pos /= neighbours
            self.vel[0] += (avg_x_pos - self.pos[0]) * self.centering_factor
            self.vel[1] += (avg_y_pos - self.pos[1]) * self.centering_factor
        # otherwise circle around point
        elif self.attack_timer >= 0:
            # multiply by random(0.5, 1) to add randomness to circling path
            self.vel[0] += (self.circling_pos[0] - self.pos[0]) * self.circling_factor * randint(5, 10) / 10
            self.vel[1] += (self.circling_pos[1] - self.pos[1]) * self.circling_factor * randint(5, 10) / 10

        # - steer away from screen edges -
        # left margin
        if self.pos[0] < self.screen_margin:
            self.vel[0] = self.vel[0] + self.turn_factor
        # right margin
        elif self.pos[0] > self.surface.get_width() - self.screen_margin:
            self.vel[0] = self.vel[0] - self.turn_factor
        # bottom margin
        if self.pos[1] > self.surface.get_height() - self.screen_margin:
            self.vel[1] = self.vel[1] - self.turn_factor
        # top margin
        elif self.pos[1] < self.screen_margin:
            self.vel[1] = self.vel[1] + self.turn_factor

        # - set speed within bounds -
        speed = math.sqrt(self.vel[0] ** 2 + self.vel[1] ** 2)
        # find fraction of speed each vel component makes up then multiply to cap at max or min speed
        # circling has separate cap to normal movement
        if speed > self.circling_max_speed and self.attack_timer > 0:
            self.vel[0] = (self.vel[0] / speed) * self.circling_max_speed
            self.vel[1] = (self.vel[1] / speed) * self.circling_max_speed
        elif speed > self.max_speed:
            self.vel[0] = (self.vel[0] / speed) * self.max_speed
            self.vel[1] = (self.vel[1] / speed) * self.max_speed
        elif speed < self.min_speed:
            self.vel[0] = (self.vel[0] / speed) * self.min_speed
            self.vel[1] = (self.vel[1] / speed) * self.min_speed

        # - apply velocity and wind -
        # wind is separate force to boid velocity (external force)
        self.pos[0] += self.vel[0] + wind[0]
        self.pos[1] += self.vel[1] + wind[1]

        # - calculate angle (for rendering) -
        self.rot_deg = math.degrees(math.atan2(self.vel[0], self.vel[1]))

    def draw(self):
        point_ahead = 12
        point_sides = 4
        outline = [
            # point ahead
            [self.pos[0] + math.sin(math.radians(self.rot_deg)) * point_ahead,
             self.pos[1] + math.cos(math.radians(self.rot_deg)) * point_ahead],
            # point side1
            [self.pos[0] + math.sin(math.radians(self.rot_deg + 90)) * point_sides,
             self.pos[1] + math.cos(math.radians(self.rot_deg + 90)) * point_sides],
            # point side2
            [self.pos[0] + math.sin(math.radians(self.rot_deg - 90)) * point_sides,
             self.pos[1] + math.cos(math.radians(self.rot_deg - 90)) * point_sides]
        ]
        pygame.draw.polygon(self.surface, "orange", outline)