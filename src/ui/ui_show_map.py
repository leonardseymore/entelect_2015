import tkFileDialog
from ui.widgets import *
from ai.entelect import *
from ai.strategy import *
from ai.domain import *

# scale up the renderer
RENDER_SCALE_FACTOR = 32

# GUI application
class Application(Frame):
    game_state_file = None
    game_state = None
    game_states = None
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
        self.windows['prediction_info'] = KeyValueWindow(master, 'Prediction Information', None, '400x300')
        self.windows['player1_info'] = KeyValueWindow(master, 'Player 1 Information', lambda: self.game_state['Players'][0])
        self.windows['player2_info'] = KeyValueWindow(master, 'Player 2 Information', lambda: self.game_state['Players'][1])

    # file dialog to load game state file
    def open_state_file(self):
        filename = tkFileDialog.askopenfilename(initialdir=REPLAY_DIR, filetypes=[("State files", "state.json")])
        if filename:
            self.load_state_file(filename)

    # file dialog to load game state file
    def predict_states(self):
        print_predicted_states(State.from_game_state(self.game_state))

    # file dialog to load game state file
    def load_state_file(self, filename):
        self.game_state_file = filename
        self.game_states = load_harness_replay_states(filename)
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
        self.labels['RoundNumber'].set('Round: %d/%d' % (self.game_state['RoundNumber'], self.game_state['RoundLimit']))
        self.redraw_canvas()

    # redraw canvas
    def redraw_canvas(self):
        if not self.game_state:
            return

        self.canvas.delete(ALL)
        for layer in self.layers:
            if layer.enabled.get():
                layer.load_game_state(self.game_state)

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
        state_menu.add_command(label="Predict States", command=self.predict_states)
        menu.add_cascade(label='State', menu=state_menu)

        layer_menu = Menu(menu, tearoff=0)
        for layer in self.layers:
            layer_menu.add_checkbutton(label=layer.name, variable=layer.enabled, command=self.redraw_canvas)
        menu.add_cascade(label='Layers', menu=layer_menu)

        self.master.config(menu=menu)

# frame to render on a canvas layer
class Layer():
    application = None
    canvas = None
    name = None
    enabled = None
    callback = None
    game_state = None
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
    def load_game_state(self, game_state):
        self.game_state = game_state
        self.render(self.canvas)

    # base class to implement layer specific
    def render(self, canvas):
        return


# frame to render game cells
class LayerCellBase(Layer):

    # reload canvas with new game state
    def render(self, canvas):
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

    def render(self, canvas):
        LayerCellBase.render(self, canvas)

    def delete_entities(self, canvas):
        for entity in self.entities:
            canvas.delete(entity)
        self.entities = []

    def cell_clicked(self, row, column):
        cell = self.game_state['Map']['Rows'][row][column]
        self.application.windows['cell_info'].show(cell)
        self.application.windows['cell_info'].get_value = lambda : self.game_state['Map']['Rows'][row][column]

    def render_cell(self, canvas, cell, column_index, row_index, left, top, right, bottom):
        if not cell:
            return

        player_number = cell['PlayerNumber']
        if not player_number > 0:
            return

        rect = canvas.create_rectangle(left, top, right, bottom, activewidth=2)
        self.entities.append(rect)
        canvas.tag_bind(rect, '<ButtonPress-1>', lambda event, row=row_index, column=column_index: self.cell_clicked(row, column))
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

    def render(self, canvas):
        LayerCellBase.render(self, canvas)

    def delete_labels(self, canvas):
        for label in self.labels:
            canvas.delete(label)
        self.labels = []

    def render_cell(self, canvas, cell, column_index, row_index, left, top, right, bottom):
        symbol = cell_to_symbol(cell)
        if not symbol == WALL_SYMBOL:
            label = canvas.create_text(left + RENDER_SCALE_FACTOR / 2, top + RENDER_SCALE_FACTOR / 2, text=symbol, state=DISABLED)
            self.labels.append(label)

# boostrap application
root = Tk()
root.resizable(0,0)
app = Application(master=root)
root.mainloop()
