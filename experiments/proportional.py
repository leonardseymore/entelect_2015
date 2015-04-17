from copy import deepcopy

# facts
facts = {'a':100} 

# functions
def x(n, facts):
	facts['a'] += n
	
def y(n, facts):
	facts['a'] -= n
	
def z(n, facts):
	return
	
funcs = {'x':x, 'y':y, 'z':z}

# check proportions
def test_proportions(func, input):
	tmp_facts = deepcopy(facts)
	func(input, tmp_facts)
	
	for f in facts:
		if tmp_facts[f] == facts[f]:
			print '%s not related to %s' % (func, f)
		elif tmp_facts[f] > facts[f]:
			print '%s is proportional to %s' % (func, f)
		else:
			print '%s is inversely proportional to %s' % (func, f)
			
test_proportions(x, 10);
test_proportions(y, 10);
test_proportions(z, 10);
