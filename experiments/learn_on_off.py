# good if value is 100, bad if value is 0

# ai has actions, based on the available actions it must learn what results on a better score
# in this case we want to teach the computer machine that the closer we get to a Good score the better
def pick_number(n):
	facts['value'] = n
	
actions = {
	'pick_number':
	{'func':pick_number, 'inputs':range(0,101)}
}

# there are facts in the system which determine the current state of the world
facts = {'value':100}

# the ai can evaluate the score based on the actions
def evaluate():
	score = facts['value']	
	return score

# performing an action changes the facts of the system so the ai needs to evaluate how these actions 
# affect the outcome	
action_results = []

def pick_input(action):
	inputs = action['inputs']
	
	if len(action_results) == 0:
		
	else:
	
	best_result = action_results[0]
	
	return inputs[100]
	
def perform_action(action):
	input = pick_input(action)
	actions[k]['func'](input)
	return input

def pick_action():
	return actions['pick_number']
	

action = pick_action()
input = perform_action(action)
output = evaluate()
result = {'input':input, 'output':output}
action_results.append(result)
sorted(action_results, key=lambda result: result['output'])   
	
print facts['value']
print action_results
if facts['value'] == 100:
	print 'Good'
else:
	print 'Bad'	