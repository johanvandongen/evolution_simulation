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
from camera import Camera
from entity import Organism, Food

pygame.font.init()
MENU_Y_HEIGHT = 700 #650 # Height that seperates simulation from options tab
MENU_COLOR = (42, 205, 211)
MENU_TEXT_COLOR = (255, 0, 0)
FPS = 30

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

class Map():
    def __init__(self):
        self.INTERNAL_SURFACE_SIZE = (2500, 2500)
        self.INTERNAL_SURFACE_SIZE_VECTOR = pygame.math.Vector2(self.INTERNAL_SURFACE_SIZE)

map = Map()
settings = Settings()
camera = Camera(0.8, settings, map)
all_orgsanism_dictonary = {}

# Run simulation
def main(genomes, config): 
    global generation
    generation += 1 
    
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
        organisms.append(Organism(new_size, new_speed, new_vision, random.randrange(0, map.INTERNAL_SURFACE_SIZE[0]), MENU_Y_HEIGHT, g.key, g.parent_key1, g.parent_key2, g))
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
        foods.append(Food("green", map))

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
                        organism.click(stats, win, camera, map)
        
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