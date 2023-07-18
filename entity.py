import os
import random
import math
import pygame
from utils import calculate_angle, calculate_distance, calculate_angle_diff

ORG_IMG = pygame.transform.rotate(pygame.image.load(os.path.join("img", "org.png")), 270)

class Food:
    TYPE = "FOOD"
    def __init__(self, color, map):
        self.x = random.randrange(0, map.INTERNAL_SURFACE_SIZE[0])
        self.y = random.randrange(0, map.INTERNAL_SURFACE_SIZE[1]-400)
        self.size = (10,10)
        self.energy = 50
        self.color = color
        self.surface = pygame.Surface(self.size)
        self.surface.fill(color)
        self.has_been_eaten = False
    
    def draw(self, win):
        pygame.draw.circle(win, self.color, (self.x, self.y), self.size[0]/2)
        #win.blit(self.surface, (self.x, self.y))

class Organism:
    IMG = ORG_IMG
    IMG_SIZE = (25,20) # IMG ratio
    # SIZE_MUTATE = 0.05
    SIZE_MUTATE = 5
    SPEED_MUTATE = 5
    VISION_MUTATE = 2
    TYPE = "ORGANISM"
    def __init__(self, size_factor, speed_factor, vision_factor, pos_x, pos_y, key, parent_key1, parent_key2, genome_ref):
        self.x = pos_x
        self.y = pos_y
        self.key = key
        self.parent_key1 = parent_key1
        self.parent_key2 = parent_key2
        self.genome_ref = genome_ref
        # self.size_factor = round(size_factor + random.randrange(-1/self.SIZE_MUTATE,1/self.SIZE_MUTATE)*(self.SIZE_MUTATE*self.SIZE_MUTATE), 3)
        self.size_factor = round(size_factor + random.randrange(int(-self.SIZE_MUTATE), int(self.SIZE_MUTATE))/100, 3)
        self.speed_factor = random.randrange(int(speed_factor-self.SPEED_MUTATE), int(speed_factor+self.SPEED_MUTATE))
        self.size = (self.IMG_SIZE[0]*self.size_factor,self.IMG_SIZE[1]*self.size_factor) # Maintain size ratio
        self.img = pygame.transform.scale(self.IMG, self.size)
        self.speed = max(1, min(15, round(5 + self.speed_factor/10, 2)))
        self.energy = 100
        self.angle = 0
        self.max_health = round(100*self.size_factor, 3)
        self.health = self.max_health
        self.vision_factor = random.randrange(int(vision_factor-self.VISION_MUTATE), int(vision_factor+self.VISION_MUTATE))
        self.vision_angle = max(1, min(180, round(90 + self.vision_factor)))
        self.vision_radius = min(75, round(90/self.vision_angle * 50))
        self.living_cost = round(2 * self.size_factor, 1)
        self.move_cost = round((self.speed/5)*self.size_factor, 2)
        self.eat_radius = round(10 * self.size_factor, 1)
        self.half_width_vector = pygame.Vector2(self.size[0]/2, 0)
        self.surface = pygame.Surface(self.size)
        self.surface.fill("black")
        self.rect = pygame.Rect(self.x, self.y, self.size[0], self.size[1])

    def move_forward(self):
        self.x = self.x + self.speed * math.cos(self.angle * math.pi / 180)
        self.y = self.y + self.speed * math.sin(self.angle * math.pi / 180)
        if self.energy > 0:
            self.energy -= self.move_cost 

    def turn_left(self):
        self.angle -= 5
        self.angle %= 360
            
    def turn_right(self):
        self.angle += 5
        self.angle %= 360

    def draw(self, win, settings):
        # win.blit(self.surface, (self.x, self.y)) # black rect box of org

        # Rectangle with org as center, the vision arc will be drawn according to this rect
        if settings.draw_vision_lines:
            self.rect = pygame.Rect(self.x-self.vision_radius*2*0.5+self.size[0]*0.5, self.y-self.vision_radius*2*0.5+self.size[0]*0.5, self.vision_radius*2, self.vision_radius*2)
            pygame.draw.arc(win, (0,0,0), self.rect, -(self.vision_angle*math.pi/180)-(self.angle*math.pi/180), (self.vision_angle*math.pi/180)-(self.angle*math.pi/180))
        
        # Draw organism
        rotated_image = pygame.transform.rotate(self.img, -self.angle)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft = (self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)
        
        # Draw center point of organism (opt)
        pygame.draw.circle(win, (255,0,0), (self.img.get_rect(topleft = (self.x, self.y)).center), 2)
        
        # Draw mouth point of organism (opt)
        # center = pygame.Vector2()
        # center.xy = self.img.get_rect(topleft = (self.x, self.y)).center 
        # mouth = pygame.Vector2()
        # mouth.xy = center+self.half_width_vector.rotate(self.angle)
        # pygame.draw.circle(win, (255,0,0), mouth.xy, 2)

    def collides(self, food):
        # Mouth is a point at the 'mouth' position (middle right of the image starting pos)
        center = pygame.Vector2()
        center.xy = self.img.get_rect(topleft = (self.x, self.y)).center 
        mouth = pygame.Vector2()
        mouth.xy = center+self.half_width_vector.rotate(self.angle)

        if ((mouth.x - (food.x))**2 + (mouth.y - (food.y))**2) < self.eat_radius**2:
            return True
        return False
    
    def reach(self, food):
        # vision lines from mouth
        center = pygame.Vector2()
        center.xy = self.img.get_rect(topleft = (self.x, self.y)).center 
        # Mouth is a point at the 'mouth' position (middle right of the image starting pos)
        mouth = pygame.Vector2()
        mouth.xy = center+self.half_width_vector.rotate(self.angle)
        org_x, org_y = mouth.xy

        # vision lines from center
        # org_x, org_y = self.img.get_rect(topleft = (self.x, self.y)).center     

        # First check if food is in specified radius
        if (org_x - (food.x))**2 + (org_y - (food.y))**2 < (self.vision_radius)**2:

            # Now check if the food is in the right semicircle
            # (Check if food angle in vision bounds)
            food_angle = calculate_angle((org_x, org_y), (food.x, food.y), invert=-1)
            left_bound = (self.angle-self.vision_angle)%360
            right_bound = (self.angle+self.vision_angle)%360
            if (left_bound < -food_angle%360  < right_bound) or (right_bound<left_bound and not(right_bound < -food_angle%360  < left_bound)):
                # Food is now within the radius as well as the right semicircle, so its in the vision
                return [(org_x, org_y), (food.x, food.y)]

        return None # Return None if object is not in vision (distance/angle)

    def reach_other_org(self, org):
        # vision lines from mouth
        center = pygame.Vector2()
        center.xy = self.img.get_rect(topleft = (self.x, self.y)).center 
        # Mouth is a point at the 'mouth' position (middle right of the image starting pos)
        mouth = pygame.Vector2()
        mouth.xy = center+self.half_width_vector.rotate(self.angle)
        org_x, org_y = mouth.xy

        # vision lines from center
        # org_x, org_y = self.img.get_rect(topleft = (self.x, self.y)).center

        # other_org_x = org.x
        # other_org_y = org.y
        other_org_x, other_org_y = org.img.get_rect(topleft = (org.x, org.y)).center

        # First check if food is in specified radius
        if (org_x - (other_org_x))**2 + (org_y - (other_org_y))**2 < (self.vision_radius)**2:

            # Now check if the food is in the right semicircle
            # (Check if food angle in vision bounds)
            food_angle = calculate_angle((org_x, org_y), (other_org_x, other_org_y), invert=-1)
            left_bound = (self.angle-self.vision_angle)%360
            right_bound = (self.angle+self.vision_angle)%360
            if (left_bound < -food_angle%360  < right_bound) or (right_bound<left_bound and not(right_bound < -food_angle%360  < left_bound)):
                # Food is now within the radius as well as the right semicircle, so its in the vision
                return [(org_x, org_y), (other_org_x, other_org_y)]

        return None # Return None if object is not in vision (distance/angle)
    
    # When an organism is clicked with mouse, do something here
    def click(self, stats_screen, win, camera, map):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        cam_offset_x = ((map.INTERNAL_SURFACE_SIZE_VECTOR[0]*camera.zoom_scale)/2 - win.get_size()[0]/2 - camera.offset.x)
        cam_offset_y = ((map.INTERNAL_SURFACE_SIZE_VECTOR[1]*camera.zoom_scale)/2 - win.get_size()[1]/2 - camera.offset.y)
        mouse_x += cam_offset_x
        mouse_y += cam_offset_y
        mouse_x *= 1/camera.zoom_scale  # no idea why this calculation is needed, but based on testing and observations 
        mouse_y *= 1/camera.zoom_scale  # I found that this was needed.
        if self.rect.collidepoint(mouse_x, mouse_y):
            stats_screen.set_organism_reference(self)
    
    # Ongoing organism processes (no action needed)
    def live(self):
        if self.energy < 5:
            if self.health < 2:
                self.health = 0
            else:
                self.health -= 2
        if self.energy > 0:
            self.energy -= self.living_cost #0.5 # Pay to live bitch