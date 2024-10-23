import pygame
from random import randint
import math
from support import get_distance


class Flock:
    def __init__(self, surface, flock_size):
        self.surface = surface
        self.boids = [Boid(self.surface) for b in range(flock_size)]

    def update(self):
        for b in self.boids:
            b.update(self.boids)

    def draw(self):
        for b in self.boids:
            b.draw()


class Boid:
    def __init__(self, surface):
        self.surface = surface
        self.rot_deg = 0
        self.pos = [randint(0, surface.get_width()), randint(0, surface.get_height())]  # x, y
        self.vel = [1, 1]  # x, y
        self.protected_r = 10  # protected distance to steer away from other boids
        self.visual_r = 50  # distance boid can see other boids
        self.turn_factor = 0.1   # 0.1 or 0.05 amount boid turns (multiplier)
        self.screen_margin = 500  # 200 margin from screen edge before turning
        self.min_speed = 1
        self.max_speed = 5  # 3 or 5
        self.matching_factor = 0.02  # loose 0.02 or 0.05 tight, tend towards average velocity (multiplier)
        self.centering_factor = 0.001  # 0.005 tend towards center of visual flock (multiplier)

    def get_pos(self):
        return self.pos

    def get_vel(self):
        return self.vel

    def update(self, boids):
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

        # - apply velocity -
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]

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