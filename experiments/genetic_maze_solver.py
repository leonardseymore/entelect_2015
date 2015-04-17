import random

# genetic algo to solve maze
maze = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1,
8, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1,
1, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1,
1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 0, 1,
1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 0, 1,
1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 0, 1,
1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 5,
1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1,
1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

class Map():
	width	= 15
	height	= 10
	enter	= [0, 2]
	exit	= [14, 7]
	map		= []
	
	def __init__(self, map):
		self.map = map
		
	def get_map_entry(self, pos):
		return self.map[pos[1] * self.width + pos[0]]
		
	def test_route(self, memory):
		return
		
	def reset_memory():
		return
	
# chromosomes
north	= 0 # 00
east	= 1 # 01
south	= 2 # 10
west	= 3 # 11

# genome
class Genome():
	bits = []
	fitness = 0
	def __init__(self, length):
		i = 0
		while i < length:
			self.bits.append(random.randint(0, 1))
			i = i + 1
	
# genetic algoritm
class Ga():
	genomes				= []	
	population_size		= 0
	crossover_rate		= 0
	mutation_rate		= 0
	chromosome_length	= 0
	gene_length			= 0
	fittest_genome		= 0
	best_fitness_score	= 0
	total_fitness_score	= 0
	generation			= 0
	map					= None
	busy				= false
	
	
	def __init__(self):
		return
	