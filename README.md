# Evolution Simulation
Evolution simulation in pygame using NEAT.

Each generation a batch of organisms is spawned on a map full of food. The organisms' actions are controlled by a neural network which determines whether the organism will move left, right or forward, based on the information of the closest food object within their vision.

The neural networks, as well as the physical traits of an organism, evolve over time, as each generation the best performing organisms are selected and bred to create the population for the next generation.

## Usage
Install all required packages by running:

`pip install -r requirements.txt`

After installing the required dependencies, you can run the project by typing the following command in the root folder:

`main.py`

### Simulation controls
- Press `ESC` to close and exit the program
- Press `Q` to zoom in
- Press `E` to zoom out
- Use the arrow keys to pan accross the map
- Press `SPACE` to pause the simulation
