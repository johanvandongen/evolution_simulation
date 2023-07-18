# Standard
import imp
import time
import os
import random
import math

# Third party
import pygame
import neat
from numpy import array

# Specific
from ui import Button, draw_net2
from ui import StatsScreen
from utils import calculate_angle, calculate_distance, calculate_angle_diff
from utils import KdTree

pygame.font.init()
WIN_WIDTH = 1500
WIN_HEIGHT = 900
MENU_Y_HEIGHT = 700 #650 # Height that seperates simulation from options tab
INTERNAL_SURFACE_SIZE = (2500, 2500)
INTERNAL_SURFACE_SIZE_VECTOR = pygame.math.Vector2(INTERNAL_SURFACE_SIZE)
MENU_COLOR = (42, 205, 211)
MENU_TEXT_COLOR = (255, 0, 0)
FPS = 30
ORG_IMG = pygame.transform.rotate(pygame.image.load(os.path.join("img", "org.png")), 270)
STAT_FONT = pygame.font.SysFont("comicsans", 30)

def get_population_size_from_file():
    with open('config-feedforward.txt') as f:
        for line in f:
            if "pop_size" in line:
                test = line.split()
                return int(test[-1])

POPULATION_SIZE = get_population_size_from_file()
generation = 0

class Settings():
    def __init__(self):
        self.draw_vision_lines = True
        self.paused = False
        self.draw_nn = False
        self.draw_node_names = False

class Food:
    TYPE = "FOOD"
    def __init__(self, color):
        # self.x = random.randrange(0, WIN_WIDTH)
        # self.y = random.randrange(0, MENU_Y_HEIGHT)
        self.x = random.randrange(0, INTERNAL_SURFACE_SIZE[0])
        self.y = random.randrange(0, INTERNAL_SURFACE_SIZE[1]-400)
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

    def draw(self, win):
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

    def reach2(self, org):
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
    def click(self, stats_screen, win):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        cam_offset_x = ((INTERNAL_SURFACE_SIZE_VECTOR[0]*camera.zoom_scale)/2 - win.get_size()[0]/2 - camera.offset.x)
        cam_offset_y = ((INTERNAL_SURFACE_SIZE_VECTOR[1]*camera.zoom_scale)/2 - win.get_size()[1]/2 - camera.offset.y)
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

class Camera:
    def __init__(self, zoom_scale):
        self.zoom_scale = zoom_scale
        self.scale_factor = 0.1
        self.max_zoom_level = 2.2
        self.camera_move_speed = 50
        self.offset = pygame.math.Vector2(100,500)
        self.internal_surface = pygame.Surface(INTERNAL_SURFACE_SIZE, pygame.SRCALPHA)

    def scale_up(self):
        if self.zoom_scale <= self.max_zoom_level:
            self.zoom_scale += self.scale_factor
        self.zoom_scale = round(self.zoom_scale, 2)
    
    def scale_down(self):
        if self.zoom_scale >= 2*self.scale_factor:
            self.zoom_scale -= self.scale_factor
        self.zoom_scale = round(self.zoom_scale, 2)

    def move_camera_left(self):
        self.offset.x += self.camera_move_speed
    
    def move_camera_right(self):
        self.offset.x -= self.camera_move_speed
    
    def move_camera_up(self):
        self.offset.y += self.camera_move_speed

    def move_camera_down(self):
        self.offset.y -= self.camera_move_speed
    
    def draw_window(self, win, stats, buttons, foods, organisms, vision_lines, angle_difference_stat, generation, config): 
        
        # Clear everything
        win.fill((0,0,0))
        self.internal_surface.fill((255,255,255)) 
        
        # Draw simulation on surface
        for food in foods:
            if food.has_been_eaten == False:
                food.draw(self.internal_surface)
        for organism in organisms:
            organism.draw(self.internal_surface)
        for line in vision_lines:
            pygame.draw.line(self.internal_surface, "black", line[0], line[1], 2) 
        stats.draw_selected_org(self.internal_surface)

        # scale the surface
        scaled_surf = pygame.transform.scale(self.internal_surface, INTERNAL_SURFACE_SIZE_VECTOR*self.zoom_scale)
        
        # Blit surface on the window
        win.blit(scaled_surf, scaled_surf.get_rect(center=(win.get_size()[0]/2+self.offset.x,win.get_size()[1]/2+self.offset.y)))
     
        # Draw menu (with stats etc) on window on top of simulation surface
        pygame.draw.rect(win, MENU_COLOR, pygame.Rect(0, MENU_Y_HEIGHT, win.get_size()[0], win.get_size()[1]-MENU_Y_HEIGHT))
        pygame.draw.line(win, "black", (0, MENU_Y_HEIGHT), (win.get_size()[0], MENU_Y_HEIGHT), 2)
        for button in buttons:
            button.draw(win) 
        
        org_count_text = STAT_FONT.render("Organisms: " + str(len(organisms)), 1, MENU_TEXT_COLOR)
        gen_text = STAT_FONT.render("Generation: " + str(generation), 1, MENU_TEXT_COLOR)
        zoom_level_text = STAT_FONT.render("Zoom: " + str(camera.zoom_scale), 1, MENU_TEXT_COLOR)
        angle_difference_text = STAT_FONT.render("Angle diff: " + str(round(angle_difference_stat)), 1, MENU_TEXT_COLOR)
        win.blit(org_count_text, (20, MENU_Y_HEIGHT)) 
        win.blit(gen_text, (20, MENU_Y_HEIGHT+30)) 
        win.blit(zoom_level_text, (20, MENU_Y_HEIGHT+60)) 
        win.blit(angle_difference_text, (20, MENU_Y_HEIGHT+90)) 

        stats.draw_stats(win) 
        
        if settings.draw_nn:
            stats.draw_net(config, win, node_names={-1:"angle diff", -2:"distance", 0:"forward", 1:"left", 2:"right"}, draw_node_names=settings.draw_node_names)
        
        pygame.display.update()


settings = Settings()
camera = Camera(0.8)
all_orgsanism_dictonary = {}

# Run simulation
def main(genomes, config): 
    global generation
    generation += 1 

    # prevent the hashmap from growing to big, we only need to store the last 2/3 generations for accessing parents
    # for key in list(all_orgsanism_dictonary.keys()):
    #     if key <= (generation-5)*POPULATION_SIZE:
    #         del all_orgsanism_dictonary[key]
    
    # Create neural nets for all genomes and also create a organism object for genomes
    nets = []
    ge = []
    organisms = []
    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        new_size = 1 if (g.parent_key1 is None or g.parent_key2 is None) else (all_orgsanism_dictonary[g.parent_key1].size_factor + all_orgsanism_dictonary[g.parent_key2].size_factor)/2
        new_speed = 0 if (g.parent_key1 is None or g.parent_key2 is None) else (all_orgsanism_dictonary[g.parent_key1].speed_factor + all_orgsanism_dictonary[g.parent_key2].speed_factor)/2
        new_vision = 0 if (g.parent_key1 is None or g.parent_key2 is None) else (all_orgsanism_dictonary[g.parent_key1].vision_factor + all_orgsanism_dictonary[g.parent_key2].vision_factor)/2
        organisms.append(Organism(new_size, new_speed, new_vision, random.randrange(0, INTERNAL_SURFACE_SIZE[0]), MENU_Y_HEIGHT, g.key, g.parent_key1, g.parent_key2, g))
        all_orgsanism_dictonary[g.key] = organisms[-1]
        g.fitness = 0
        ge.append(g)
        #print( g.key, " = ", g.parent_key1, " + ", g.parent_key2)

    # Initialisations
    run = True
    win = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    clock = pygame.time.Clock()
    button_pause = Button("Pause", (240, MENU_Y_HEIGHT+10), font_size=25)
    button_change_style = Button("Draw vision", (240, MENU_Y_HEIGHT+50), font_size=25, pressed=not settings.draw_vision_lines)
    button_draw_nn = Button("Draw nn", (240, MENU_Y_HEIGHT+90), font_size=25, pressed=not settings.draw_nn)
    button_draw_nn_node_names = Button("Node names", (350, MENU_Y_HEIGHT+90), font_size=25, pressed=not settings.draw_node_names)
    button_exit = Button("Exit", (win.get_size()[0] - 100, 10), font_size=25, pressed=False)
    foods = []
    
    # Generate initial food
    for _ in range(800):
        foods.append(Food("green"))

    all_food = [[food.x,food.y, food] for food in foods]
    all_org = [[*org.img.get_rect(topleft = (org.x, org.y)).center, org] for org in organisms]
    # all_food.extend(all_org)
    food_kd_tree = KdTree(all_food)
        
    # Show stats for organism (organism can be chanhed in the simulation by clicking)
    stats = StatsScreen(organisms[0], win.get_size()[0], win.get_size()[1], MENU_Y_HEIGHT, MENU_TEXT_COLOR)
    
    # Game loop - Or with neat, this is the fitness function
    while run:
        clock.tick(FPS)

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
            
            if button_exit.click(event):
                run = False
                pygame.quit()
                quit()
            
            if button_pause.click(event):
                settings.paused = not settings.paused
            
            if button_change_style.click(event):
                settings.draw_vision_lines = not settings.draw_vision_lines
            
            if button_draw_nn.click(event):
                settings.draw_nn = not settings.draw_nn
            
            if button_draw_nn_node_names.click(event):
                settings.draw_node_names = not settings.draw_node_names
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False
                    pygame.quit()
                    quit()
                if event.key == pygame.K_SPACE:
                    settings.paused = not settings.paused
                    button_pause.increase_tick() # Tick determines button color
                if event.key == pygame.K_q:
                    camera.scale_up()
                if event.key == pygame.K_e:
                    camera.scale_down()
                if event.key == pygame.K_UP:
                    camera.move_camera_up()
                if event.key == pygame.K_DOWN:
                    camera.move_camera_down()
                if event.key == pygame.K_LEFT:
                    camera.move_camera_left()
                if event.key == pygame.K_RIGHT:
                    camera.move_camera_right()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.mouse.get_pressed()[0]:
                    for organism in organisms:
                        organism.click(stats, win)
        
        if settings.paused:
            camera.draw_window(win, stats, [button_pause, button_change_style, button_draw_nn, button_draw_nn_node_names, button_exit], foods, organisms, vision_lines, angle_difference_stat, generation, config)
            continue
        
        # Stop game when there are no more organisms (neat will then start new generation)
        if len(organisms) <= 0:
            run = False
            break
        
        # Handle organism interactions (ie vision, colission, death)
        vision_lines = []
        angle_difference_stat = 0
        for i, organism in enumerate(organisms):
            organism.live() # Costs of living (energy drainage, money, depressions etc.. you know)

            # ---- food collision loop using KD-tree ~O(n log n) 
            min_dist = 100 # No min distant (this number is larger that organism view distance)
            closest_object = None # Closest object is initially None
            org_center_x, org_center_y = organism.img.get_rect(topleft = (organism.x, organism.y)).center
            search_box = array([[org_center_x-organism.vision_radius, org_center_x+organism.vision_radius], [org_center_y-organism.vision_radius, org_center_y+organism.vision_radius]])
            for point in food_kd_tree.range_search(search_box):
                food = point[2]

                if food.TYPE == "FOOD":
                    # If food has already been eaten skip this iteration
                    if food.has_been_eaten:
                        continue

                    if organism.collides(food) == True:
                        if food.TYPE == "FOOD":
                            organism.energy += food.energy
                            ge[i].fitness += 5 
                            food.has_been_eaten = True
                    
                    # Get coordinates of objects that are in vision (can be drawn later)
                    object_in_vision_coords = organism.reach(food)
                    if object_in_vision_coords != None:
                        # Draw vision lines or not
                        if settings.draw_vision_lines:
                            vision_lines.append(object_in_vision_coords)
                        
                        # Change closest_object if the current object is closer
                        dist = calculate_distance(object_in_vision_coords[0], object_in_vision_coords[1])
                        if dist < min_dist:
                            min_dist = dist
                            closest_object = object_in_vision_coords

                # try to do something with other organisms in reach
                # not done yet.
                if food.TYPE == "ORGANISM":
                    pass
            
            # Food loop done, process organism further (fitness, inputs, determine output)
            if closest_object is not None and (abs((organism.angle%360)-calculate_angle(closest_object[0], closest_object[1]))) < 7:
                ge[i].fitness += 0.2
            ge[i].fitness += 1
                
            # Provide AI input for organism
            if closest_object is not None:
                angle_difference = calculate_angle_diff(organism.angle, calculate_angle(closest_object[0], closest_object[1], invert=1))
                ge[i].fitness += (organism.vision_radius/50)/(calculate_distance(closest_object[0], closest_object[1])+1)
                output = nets[i].activate([angle_difference, calculate_distance(closest_object[0], closest_object[1])])
            else:
                angle_difference = 0
                ge[i].fitness -= 0.05
                output = nets[i].activate([angle_difference, 1000])

            # show angle difference of selected org in stat screen
            if organism == stats.organism:
                angle_difference_stat = angle_difference

            # AI determines organism output
            if output[0] > 0.5:
                organism.move_forward()
            if output[1] > 0.5:
                organism.turn_left()
            elif output[2] > 0.5:
                organism.turn_right()

            if organism.health <= 0:
                ge[i].fitness -= 1
                organisms.pop(i)
                nets.pop(i)
                ge.pop(i)

        # Draw everything
        camera.draw_window(win, stats, [button_pause, button_change_style, button_draw_nn, button_draw_nn_node_names, button_exit], foods, organisms, vision_lines, angle_difference_stat, generation, config)

class MyGenome(neat.DefaultGenome):

    def __init__(self, key):
        super().__init__(key)
        self.parent_key1 = None
        self.parent_key2 = None

    def configure_crossover(self, genome1, genome2, config):
        self.parent_key1 = genome1.key
        self.parent_key2 = genome2.key
        super().configure_crossover(genome1, genome2, config)
    
# Run neat algorithm
def run(config_path):
    config = neat.config.Config(MyGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)
    
    p = neat.Population(config) # Create population based on config file
    
    # Show statistics
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # main is fitness function, but besides calculating the fitness, 'main' also draws to screen (the simulation)
    winner = p.run(main, 200) 

# start neat algorithm
if __name__ == "__main__":
    local_directory = os.path.dirname(__file__)
    config_path = os.path.join(local_directory, "config-feedforward.txt")
    run(config_path)