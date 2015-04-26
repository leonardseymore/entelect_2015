import tkFileDialog
from ui.widgets import *
from ai.entelect import *

# scale up the renderer
RENDER_SCALE_FACTOR = 32

# GUI application
class Application(Frame):
    game_state_file = None
    game_state = None
    game_states = None
    blackboard = None
    blackboards = None
    round_number = 0

    windows = {}

    labels = {}
    layers = []
    canvas = None

    def __init__(self, master=None):
        Frame.__init__(self, master)
        master.wm_title('Entelect 2015 UI Toolkit')
        master.iconbitmap('resources/invader.ico')
        self.labels['RoundNumber'] = StringVar()
        self.create_widgets()
        self.create_menu()
        self.windows['game_info'] = KeyValueWindow(master, 'Game Information', lambda: self.game_state)
        self.windows['cell_info'] = KeyValueWindow(master, 'Cell Information', None, '400x300')
        self.windows['player1_info'] = KeyValueWindow(master, 'Player 1 Information', lambda: self.game_state['Players'][0])
        self.windows['player2_info'] = KeyValueWindow(master, 'Player 2 Information', lambda: self.game_state['Players'][1])
        self.windows['blackboard'] = BlackboardWindow(master, 'Blackboard', lambda: self.blackboard)

        register('cell_clicked', self)

    # file dialog to load game state file
    def open_state_file(self):
        filename = tkFileDialog.askopenfilename(initialdir=REPLAY_DIR, filetypes=[("State files", "state.json")])
        if filename:
            self.load_state_file(filename)

    # file dialog to load game state file
    def load_state_file(self, filename):
        self.game_state_file = filename
        self.game_states = load_harness_replay_states(filename)
        self.blackboards = []
        for game_state in self.game_states:
            blackboard = Blackboard()
            blackboard.set('game_state', game_state)
            blackboard.set('rounds_in_replay', len(self.game_states))
            field_analyst.run(blackboard)
            alien_expert.run(blackboard)
            self.blackboards.append(blackboard)
        round_number = int(os.path.basename(os.path.dirname(filename)))
        self.load_round(round_number)

    # loads a state based on round number
    def load_round(self, round_number):
        if not self.game_states:
            return
        if round_number >= len(self.game_states):
            return
        self.round_number = round_number

        self.game_state = self.game_states[round_number]
        self.blackboard = self.blackboards[round_number]
        self.labels['RoundNumber'].set('Round: %d/%d' % (self.blackboard.get('round_number'), self.blackboard.get('round_limit')))
        self.redraw_canvas()

    # redraw canvas
    def redraw_canvas(self):
        if not self.game_state:
            return

        self.canvas.delete(ALL)
        for layer in self.layers:
            if layer.enabled.get():
                layer.load_game_state(self.game_state, self.blackboard)

    # tries to load the previous state
    def load_prev_state(self):
        if not self.game_state:
            return
        round_number = self.game_state['RoundNumber']
        if round_number == 0:
            return
        self.load_round(round_number - 1)

    # tries to load the next state
    def load_next_state(self):
        if not self.game_state:
            return
        round_number = self.game_state['RoundNumber']
        self.load_round(round_number + 1)

    # handler called when clicking on a cell
    def handle_cell_clicked(self, event):
        row = event.payload['row']
        column = event.payload['column']
        cell = self.game_state['Map']['Rows'][row][column]
        self.windows['cell_info'].show(cell)
        self.windows['cell_info'].get_value = lambda : self.game_state['Map']['Rows'][row][column]

    def reload_all_windows(self):
        if not self.game_state:
            return
        for key in self.windows:
            window = self.windows[key]
            window.reload()

    # initialize application widgets
    def create_widgets(self):
        frame = Frame(self.master)
        frame.grid(sticky=NSEW)

        self.canvas = Canvas(frame, width=MAP_WIDTH * RENDER_SCALE_FACTOR, height=MAP_HEIGHT * RENDER_SCALE_FACTOR, bd=1, relief=SUNKEN)
        self.canvas.grid(row=0, sticky=EW)
        self.layers.append(LayerBase(self))
        self.layers.append(LayerEntities(self))
        self.layers.append(LayerAlienBBox(self))
        self.layers.append(LayerAlienBBoxPredictions(self))
        self.layers.append(LayerLabels(self))

        nav_frame = Frame(frame)
        nav_frame.grid(sticky=EW, row=1)
        Button(nav_frame, text='<', command=self.load_prev_state).grid(row=0, sticky=W)
        Button(nav_frame, text='>', command=self.load_next_state).grid(row=0, column=1, sticky=E)
        Label(nav_frame, textvariable=self.labels['RoundNumber']).grid(row=0, column=2, sticky=W)
        self.master.bind('<Left>', lambda event: self.load_prev_state())
        self.master.bind('<Right>', lambda event: self.load_next_state())
        self.master.bind('<Control-r>', lambda event: self.reload_all_windows())

    def create_menu(self):
        menu = Menu(self.master)

        file_menu = Menu(menu, tearoff=0)
        file_menu.add_command(label="Load State File", command=self.open_state_file)
        file_menu.add_command(label="Exit", command=self.master.quit)
        menu.add_cascade(label='File', menu=file_menu)

        state_menu = Menu(menu, tearoff=0)
        state_menu.add_command(label="Show Game Info", command=lambda: self.windows['game_info'].show(self.game_state))
        state_menu.add_command(label="Show Player 1 Info", command=lambda: self.windows['player1_info'].show(self.game_state['Players'][0]))
        state_menu.add_command(label="Show Player 2 Info", command=lambda: self.windows['player2_info'].show(self.game_state['Players'][1]))
        menu.add_cascade(label='State', menu=state_menu)

        layer_menu = Menu(menu, tearoff=0)
        for layer in self.layers:
            layer_menu.add_checkbutton(label=layer.name, variable=layer.enabled, command=self.redraw_canvas)
        menu.add_cascade(label='Layers', menu=layer_menu)

        expert_menu = Menu(menu, tearoff=0)
        expert_menu.add_command(label='Show Blackboard', command=lambda: self.windows['blackboard'].show(self.blackboard))
        menu.add_cascade(label='Blackboard', menu=expert_menu)

        self.master.config(menu=menu)

# frame to render on a canvas layer
class Layer():
    application = None
    canvas = None
    name = None
    enabled = None
    callback = None
    game_state = None
    blackboard = None
    width = 0
    height = 0

    def __init__(self, application, name, enabled=True):
        self.application = application
        self.canvas = application.canvas
        self.enabled = BooleanVar(self.canvas)
        self.enabled.set(enabled)
        self.name = name
        self.width = MAP_WIDTH * RENDER_SCALE_FACTOR
        self.height = MAP_HEIGHT * RENDER_SCALE_FACTOR

    # reload canvas with new game state
    def load_game_state(self, game_state, blackboard):
        self.game_state = game_state
        self.blackboard = blackboard
        self.render(self.canvas, blackboard)

    # base class to implement layer specific
    def render(self, canvas, blackboard):
        return


# frame to render game cells
class LayerCellBase(Layer):

    # reload canvas with new game state
    def render(self, canvas, blackboard):
        game_map = self.game_state['Map']
        for row_index, row in enumerate(game_map['Rows']):
            for column_index, cell in enumerate(row):
                self.render_cell(self.canvas, cell, column_index, row_index, column_index * RENDER_SCALE_FACTOR, row_index * RENDER_SCALE_FACTOR, column_index * RENDER_SCALE_FACTOR + RENDER_SCALE_FACTOR, row_index * RENDER_SCALE_FACTOR + RENDER_SCALE_FACTOR)

    # base class to implement layer specific
    def render_cell(self, canvas, cell, column_index, row_index, left, top, right, bottom):
        return

# frame to render game cells
class LayerBase(LayerCellBase):

    def __init__(self, application):
        Layer.__init__(self, application, 'Base')
        self.canvas.create_line(0, 0, self.width, self.height)
        self.canvas.create_line(0, self.height, self.width, 0)

    # reload canvas with new game state
    def render_cell(self, canvas, cell, column_index, row_index, left, top, right, bottom):
        rect = canvas.create_rectangle(left, top, right, bottom, state=DISABLED)
        if not cell:
            canvas.itemconfig(rect, fill='lightgrey')
            return
        if cell['Type'] == WALL:
            canvas.itemconfig(rect, fill='grey')


# entities layer
class LayerEntities(LayerCellBase):
    entities = None

    def __init__(self, canvas):
        Layer.__init__(self, canvas, 'Entities')
        self.entities = []

    def render(self, canvas, blackboard):
        LayerCellBase.render(self, canvas, blackboard)

    def delete_entities(self, canvas):
        for entity in self.entities:
            canvas.delete(entity)
        self.entities = []

    def render_cell(self, canvas, cell, column_index, row_index, left, top, right, bottom):
        if not cell:
            return

        player_number = cell['PlayerNumber']
        if not player_number > 0:
            return

        rect = canvas.create_rectangle(left, top, right, bottom, activewidth=2)
        self.entities.append(rect)
        canvas.tag_bind(rect, '<ButtonPress-1>', lambda event, row=row_index, column=column_index: dispatch(Event('cell_clicked', {'row': row, 'column': column})))
        if cell['PlayerNumber'] == 1:
            canvas.itemconfig(rect, fill='blue')
        elif cell['PlayerNumber'] == 2:
            canvas.itemconfig(rect, fill='red')

# frame to labels
class LayerLabels(LayerCellBase):
    labels = None

    def __init__(self, canvas):
        Layer.__init__(self, canvas, 'Labels')
        self.labels = []

    def render(self, canvas, blackboard):
        LayerCellBase.render(self, canvas, blackboard)

    def delete_labels(self, canvas):
        for label in self.labels:
            canvas.delete(label)
        self.labels = []

    def render_cell(self, canvas, cell, column_index, row_index, left, top, right, bottom):
        symbol = cell_to_symbol(cell)
        if not symbol == WALL_SYMBOL:
            label = canvas.create_text(left + RENDER_SCALE_FACTOR / 2, top + RENDER_SCALE_FACTOR / 2, text=symbol, state=DISABLED)
            self.labels.append(label)

# draw bounding box around aliens
class LayerAlienBBox(Layer):

    def __init__(self, canvas):
        Layer.__init__(self, canvas, 'Alien BBox')

    def render(self, canvas, blackboard):
        bbox = blackboard.get('your_alien_bbox')
        canvas.create_rectangle(bbox['left'] * RENDER_SCALE_FACTOR, bbox['top'] * RENDER_SCALE_FACTOR, (bbox['right'] + 1) * RENDER_SCALE_FACTOR, (bbox['bottom'] + 1) * RENDER_SCALE_FACTOR, outline='blue', width=2, activewidth=4)
        bbox = blackboard.get('enemy_alien_bbox')
        canvas.create_rectangle(bbox['left'] * RENDER_SCALE_FACTOR, bbox['top'] * RENDER_SCALE_FACTOR, (bbox['right'] + 1) * RENDER_SCALE_FACTOR, (bbox['bottom'] + 1) * RENDER_SCALE_FACTOR, outline='red', width=2, activewidth=4)

# draw bounding box around aliens
class LayerAlienBBoxPredictions(Layer):
    at_time = 0
    round_number = 0
    max_time = 0
    rect_time = None
    timeline_rects = None
    at_time_label = None
    your_prediction_rect = None
    enemy_prediction_rect = None
    your_bbox_predictions = None
    enemy_bbox_predictions = None
    layer_entities = None
    layer_labels = None

    def __init__(self, canvas):
        Layer.__init__(self, canvas, 'Alien BBox Predictions')
        self.at_time_label = StringVar()
        self.layer_entities = LayerEntities(canvas)
        self.layer_labels = LayerLabels(canvas)
        self.application.master.bind('<d>', lambda this=self: self.forward())
        self.application.master.bind('<a>', lambda this=self: self.back())

    def load_game_state(self, game_state, blackboard):
        Layer.load_game_state(self, game_state, blackboard)

    def render(self, canvas, blackboard):
        self.at_time = 0
        self.round_number = blackboard.get('round_number')
        self.max_time = blackboard.get('rounds_in_replay') - self.round_number - 1

        rect_back = canvas.create_rectangle(0, 0, 40, RENDER_SCALE_FACTOR, fill='purple', activefill='pink')
        canvas.tag_bind(rect_back, '<ButtonPress-1>', lambda this=self: self.first())
        canvas.create_text(20, RENDER_SCALE_FACTOR / 2 + 1, text='<<', state=DISABLED)

        rect_back = canvas.create_rectangle(40, 0, 80, RENDER_SCALE_FACTOR, fill='purple', activefill='pink')
        canvas.tag_bind(rect_back, '<ButtonPress-1>', lambda this=self: self.back())
        canvas.create_text(60, RENDER_SCALE_FACTOR / 2 + 1, text='<', state=DISABLED)

        rect_forward = canvas.create_rectangle(80, 0, 120, RENDER_SCALE_FACTOR, fill='purple', activefill='pink')
        canvas.tag_bind(rect_forward, '<ButtonPress-1>', lambda this=self: self.forward())
        canvas.create_text(100, RENDER_SCALE_FACTOR / 2 + 1, text='>', state=DISABLED)

        canvas.create_rectangle(120, 0, MAP_WIDTH * RENDER_SCALE_FACTOR, RENDER_SCALE_FACTOR, fill='grey')
        self.at_time_label = canvas.create_text(130, RENDER_SCALE_FACTOR / 2 + 1, text='No predictions', anchor=W, state=DISABLED)

        self.your_bbox_predictions = blackboard.get('your_bbox_predictions')
        self.your_prediction_rect = canvas.create_rectangle(0, 0, 0, 0, outline='purple', width=2, activewidth=4)

        self.enemy_bbox_predictions = blackboard.get('enemy_bbox_predictions')
        self.enemy_prediction_rect = canvas.create_rectangle(0, 0, 0, 0, outline='purple', width=2, activewidth=4)

        canvas.create_rectangle(0, (MAP_HEIGHT * RENDER_SCALE_FACTOR) - RENDER_SCALE_FACTOR, MAP_WIDTH * RENDER_SCALE_FACTOR, MAP_HEIGHT * RENDER_SCALE_FACTOR, width=1, fill='grey', state=DISABLED)
        round_limit = blackboard.get('round_limit')
        cell_width = (MAP_WIDTH * RENDER_SCALE_FACTOR) / float(round_limit)

        self.timeline_rects = []
        for i in range(self.round_number, blackboard.get('rounds_in_replay')):
            rect_time = canvas.create_rectangle((i + 1) * cell_width, (MAP_HEIGHT * RENDER_SCALE_FACTOR) - RENDER_SCALE_FACTOR + 1, (i + 2) * cell_width, MAP_HEIGHT * RENDER_SCALE_FACTOR, width=0, fill='purple', activefill='pink')
            if i == self.round_number:
                canvas.itemconfig(rect_time, fill='orange')
            canvas.tag_bind(rect_time, '<ButtonPress-1>', lambda this=self, t=i - self.round_number: self.to(t))
            self.timeline_rects.append(rect_time)

        self.update()

    def first(self):
        self.at_time = 0
        self.update()

    def to(self, time):
        self.at_time = time
        self.update()

    def back(self):
        if self.at_time > 0:
            self.at_time -= 1
            self.update()

    def forward(self):
        if self.at_time < self.max_time:
            self.at_time += 1
            self.update()

    def update(self):
        self.canvas.itemconfig(self.at_time_label, text='~In turns %d [round: %d]' % ((self.at_time), (self.at_time + self.round_number)))
        self.show_at_time(self.at_time, self.at_time + self.round_number)

    def show_at_time(self, t, round_number):
        print '%d - %d' % (t, round_number)
        if round_number >= len(self.application.game_states):
            return

        if self.rect_time:
            self.canvas.itemconfig(self.rect_time, width=0)
        self.canvas.itemconfig(self.timeline_rects[t], width=1)
        self.rect_time = self.timeline_rects[t]

        self.layer_entities.delete_entities(self.canvas)
        self.layer_entities.game_state = self.application.game_states[round_number]
        self.layer_labels.delete_labels(self.canvas)
        self.layer_labels.game_state = self.application.game_states[round_number]
        self.layer_entities.render(self.canvas, self.application.blackboards[round_number])
        if t < len(self.your_bbox_predictions):
            bbox = self.your_bbox_predictions[t]
            self.canvas.coords(self.your_prediction_rect,
                               bbox['left'] * RENDER_SCALE_FACTOR, bbox['top'] * RENDER_SCALE_FACTOR,
                               (bbox['right'] + 1) * RENDER_SCALE_FACTOR,
                               (bbox['bottom'] + 1) * RENDER_SCALE_FACTOR
                               )
        else:
            self.canvas.coords(self.your_prediction_rect, 0, 0, 0, 0)

        if t < len(self.enemy_bbox_predictions):
            bbox = self.enemy_bbox_predictions[t]
            self.canvas.coords(self.enemy_prediction_rect,
                               bbox['left'] * RENDER_SCALE_FACTOR, bbox['top'] * RENDER_SCALE_FACTOR,
                               (bbox['right'] + 1) * RENDER_SCALE_FACTOR,
                               (bbox['bottom'] + 1) * RENDER_SCALE_FACTOR
                               )
        else:
            self.canvas.coords(self.enemy_prediction_rect, 0, 0, 0, 0)
        self.layer_labels.render(self.canvas, self.application.blackboards[round_number])

# boostrap application
root = Tk()
root.resizable(0,0)
app = Application(master=root)
root.mainloop()
