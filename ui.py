import pygame
import random
pygame.font.init()
STAT_FONT = pygame.font.SysFont("comicsans", 30)

class Button:
    def __init__(self, text,  pos, font_size, bg_colors=["darkgreen", "red"], pressed=False):
        self.x, self.y = pos
        self.tick = 1 if pressed else 0
        self.font = pygame.font.SysFont("comicsans", font_size)
        self.colors = bg_colors
        self.bg = self.colors[self.tick]
        self.set_text(text, self.bg)
 
    def set_text(self, text, bg="black", text_color="White"):
        self.text = self.font.render(text, 1, pygame.Color(text_color))
        self.size = self.text.get_size()
        self.surface = pygame.Surface(self.size)
        self.surface.fill(bg)
        self.surface.blit(self.text, (0, 0))
        self.rect = pygame.Rect(self.x, self.y, self.size[0], self.size[1]) # collision detection
 
    def draw(self, win):
        if self.bg != self.colors[self.tick]:
            self.bg = self.colors[self.tick]
            self.surface.fill(self.bg)
            self.surface.blit(self.text, (0,0))

        win.blit(self.surface, (self.x, self.y))

    def increase_tick(self):
        self.tick = (self.tick+1) % 2
 
    def click(self, event):
        x, y = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if pygame.mouse.get_pressed()[0]:
                if self.rect.collidepoint(x, y):
                    self.increase_tick()
                    return True

class StatsScreen:
    def __init__(self, organism,  win_width, win_height, menu_height, text_color="black"):
        self.WIN_WIDTH = win_width
        self.WIN_HEIGHT = win_height
        self.MENU_Y_POS = menu_height
        self.MENU_HEIGHT = self.WIN_HEIGHT - self.MENU_Y_POS
        self.x = self.WIN_WIDTH-400
        self.margin = 10
        self.text_color = text_color
        self.border_width = 2
        self.width = 200
        self.heigth = 200 
        self.organism = organism
 
    def set_organism_reference(self, organism):
        self.organism = organism
 
    def draw_stats(self, win):
    
        # Draw physical traits
        y = self.MENU_Y_POS
        traits_list = ["size: " + str(self.organism.size_factor), "speed: " + str(self.organism.speed), "eating radius: " + str(self.organism.eat_radius), "vision radius: " + str(self.organism.vision_radius), "vision angle: " + str(self.organism.vision_angle), "max HP: " + str(self.organism.max_health)]
        for trait in traits_list:
            text = pygame.font.SysFont("comicsans", 20).render(trait, 1, self.text_color)
            win.blit(text, (self.x+self.margin, y))
            y += 20
        pygame.draw.rect(win, (0,0,0), pygame.Rect(self.x, self.MENU_Y_POS, self.width, self.heigth), self.border_width)

        # Draw organism changing stats like energy
        y = self.MENU_Y_POS
        stats_list = ["energy: "+ str(round(self.organism.energy, 2)), "angle: "+str(self.organism.angle), "health: "+str(self.organism.health)]
        for stat in stats_list:
            text = STAT_FONT.render(stat, 1, self.text_color)
            win.blit(text, (self.x+self.width+self.margin, y))
            y += 50
        pygame.draw.rect(win, (0,0,0), pygame.Rect(self.x+self.width-self.border_width, self.MENU_Y_POS, self.width, self.heigth), self.border_width)
 
    def draw_selected_org(self, surface):
        
        # Draw selected organism circle
        if self.organism.health > 0:
            pygame.draw.circle(surface, (0,0,0), (self.organism.x+self.organism.size[0]/2, self.organism.y+self.organism.size[1]/2), 20, 2)

    def draw_net(self, config, win, node_names=None, show_disabled=True, draw_node_names=False):
        NN_FONT = pygame.font.SysFont("comicsans", 10)
        genome = self.organism.genome_ref
        
        if node_names is None:
            node_names = {}

        node_positions = {}
        start_x = 100
        start_y = 50
        margin = 5
        nn_width = 100

        if False:
            pygame.draw.rect(win, (0,0,0), pygame.Rect(start_x, start_y, nn_width+20, nn_width+20), 2)

        # Get input and ouput node keys, create a position and store that
        inputs = set()
        y = start_y
        x = start_x + margin
        for k in config.genome_config.input_keys:
            inputs.add(k)
            node_positions[k] = [x,y]
            y += 50

        outputs = set()
        x = start_x + nn_width - margin
        y = start_y
        for k in config.genome_config.output_keys:
            outputs.add(k)
            node_positions[k] = [x,y]
            y += 50

        used_nodes = set(genome.nodes.keys())
        for n in used_nodes:
            if n in inputs or n in outputs:
                continue
            random.seed(n)
            x = random.randrange(start_x+2*margin, start_x+nn_width-2*margin)
            y = random.randrange(start_y+2*margin, start_y+nn_width-2*margin)
            node_positions[n] = [x,y]
            pygame.draw.circle(win, (0,0,0), (x, y), 5)

        for cg in genome.connections.values():
            if cg.enabled or show_disabled:
                input, output = cg.key
                a = node_names.get(input, str(input))
                b = node_names.get(output, str(output))
                color = 'green' if cg.weight > 0 else 'red'
                if not cg.enabled: color = 'grey' 
                width = round(1 + abs(cg.weight / 5.0))
                pygame.draw.line(win, color, node_positions[input], node_positions[output], width)

        # draw nodes and text
        y = start_y
        x = start_x + margin

        # Draw key and parent keys
        if draw_node_names and False:
            nn_key_text = NN_FONT.render("key: " + str(genome.key), 1, self.text_color)
            nn_parent_key1_text = NN_FONT.render("parent 1: " + str(genome.parent_key1), 1, self.text_color)
            nn_parent_key2_text = NN_FONT.render("parent 2: " + str(genome.parent_key2), 1, self.text_color)
            win.blit(nn_key_text, (x,y-6*margin))
            win.blit(nn_parent_key1_text, (x+50,y-6*margin))
            win.blit(nn_parent_key2_text, (x+50,y-6*margin+10))

        for k in config.genome_config.input_keys:
            pygame.draw.circle(win, (0,0,255), (x, y), 5)
            
            if draw_node_names:
                name = node_names.get(k, str(k))
                nn_text = NN_FONT.render(name, 1, self.text_color)
                win.blit(nn_text, (x-nn_text.get_width()/2,y))

            y += 50

        outputs = set()
        x = start_x + nn_width - margin
        y = start_y
        for k in config.genome_config.output_keys:
            
            pygame.draw.circle(win, (0,0,255), (x, y), 5)

            if draw_node_names:
                name = node_names.get(k, str(k))
                nn_text = NN_FONT.render(name, 1, self.text_color)
                win.blit(nn_text, (x,y))

            y += 50 

def draw_net2(config, genome, win, node_names=None, show_disabled=True):

    if node_names is None:
        node_names = {}

    node_positions = {}
    start_x = 100
    start_y = 50
    margin = 5
    nn_width = 100

    inputs = set()
    y = start_y
    x = start_x + margin
    for k in config.genome_config.input_keys:
        inputs.add(k)
        name = node_names.get(k, str(k))
        node_positions[k] = [x,y]
        pygame.draw.circle(win, (0,0,255), (x, y), 5)
        y += 50

    outputs = set()
    x = start_x + nn_width - margin
    y = start_y
    for k in config.genome_config.output_keys:
        outputs.add(k)
        node_positions[k] = [x,y]
        name = node_names.get(k, str(k))
        pygame.draw.circle(win, (0,0,255), (x, y), 5)
        y += 50

    used_nodes = set(genome.nodes.keys())
    for n in used_nodes:
        if n in inputs or n in outputs:
            continue
        x = 150#random.randrange(start_x+2*margin, start_x+nn_width-2*margin)
        node_positions[n] = [x,y]
        pygame.draw.circle(win, (0,0,0), (x, y), 5)

    for cg in genome.connections.values():
        if cg.enabled or show_disabled:
            input, output = cg.key
            a = node_names.get(input, str(input))
            b = node_names.get(output, str(output))
            color = 'green' if cg.weight > 0 else 'red'
            if not cg.enabled: color = 'grey' 
            width = round(1 + abs(cg.weight / 5.0))
            pygame.draw.line(win, color, node_positions[input], node_positions[output], width) 
