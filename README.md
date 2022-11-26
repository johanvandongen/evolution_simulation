# evolutionSimulation
Evolution simulation in pygame using NEAT.

Each generation a batch of organisms is spawned on a map full of food. The organisms' actions are controlled by a neural network which determines whether the organism will move left, right or forward, based on the information of the closest food object within their vision.

The neural networks, as well as the physical traits of an organism, evolve over time, as each generation the best performing organisms are selected and bred to create the population for the next generation.

# Uses the following libraries
<ul>
<li>neat-python</li>
<li>pygame</li>
</ul>

<b>Big note:</b>
I changed the neat-python library source code to include some fields which are needed for my code to work (bad practice).
Therefore installing the libraries wont directly make the code work. 
I still need to change that by using inheritance, but for the mean time its like this.
