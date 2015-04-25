from ai.io import *
import os.path

def is_bbox_equal(bbox1, bbox2):
    return bbox1['top'] == bbox2['top'] and bbox1['right'] == bbox2['right'] and bbox1['bottom'] == bbox2['bottom'] and bbox1['left'] == bbox2['left']

def walk_harness_replay_dir(state_files, top, names):
    state_file = join(top, 'state.json')
    if os.path.exists(state_file):
        state_files.append(state_file)

# expects top level replay directory c:\Users\leonard\entelect\Replays\0001
# or replay file  c:\Users\leonard\entelect\Replays\0001\001\state.json
def load_harness_replay_states(filename, replaytype='file'):
    if replaytype == 'dir':
        directory = filename
    elif replaytype == 'file':
        directory = dirname(dirname(filename))
    else:
        raise Exception('Unknown replay type %s' % replaytype)
    state_files = []
    walk(directory, walk_harness_replay_dir, state_files)
    states = []
    for state_file in state_files:
        states.append(load_state(state_file))
    return states
