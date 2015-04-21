from Tkinter import *
import tkFileDialog
import ai.io
import ai.entelect
import ai.event
from ai.blackboard import Blackboard
import ai.expert
from ui.widgets import *
from os.path import dirname
from os.path import join
from os.path import exists

# scale up the renderer
RENDER_SCALE_FACTOR = 20


# GUI application
class Application(Frame):
    game_state_file = None
    game_state = None
    blackboard = None

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

        ai.event.register('cell_clicked', self)

    # file dialog to load game state file
    def open_state_file(self):
        filename = tkFileDialog.askopenfilename(filetypes=[("State files", "state.json")])
        if filename:
            self.load_state_file(filename)

    # file dialog to load game state file
    def load_state_file(self, filename):
        self.game_state_file = filename
        self.game_state = ai.io.load_state(filename)
        self.blackboard = Blackboard()
        self.blackboard.set('game_state', self.game_state)
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

    # tries to load a specific state
    def load_specific_state(self, round_number):
        if not self.game_state or not (round_number >= 0 and round_number <= self.game_state['RoundLimit']):
            return
        file_to_load = dirname(dirname(self.game_state_file))
        file_to_load = join(file_to_load, str(round_number).zfill(3), 'state.json')
        if exists(file_to_load):
            self.load_state_file(file_to_load)

    # tries to load the previous state
    def load_prev_state(self):
        if not self.game_state:
            return
        round_number = self.game_state['RoundNumber']
        self.load_specific_state(round_number - 1)

    # tries to load the next state
    def load_next_state(self):
        if not self.game_state:
            return
        round_number = self.game_state['RoundNumber']
        self.load_specific_state(round_number + 1)

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

        canvas = Canvas(frame, width=ai.entelect.MAP_WIDTH * RENDER_SCALE_FACTOR, height=ai.entelect.MAP_HEIGHT * RENDER_SCALE_FACTOR, bd=1, relief=SUNKEN)
        self.canvas = canvas
        canvas.grid(row=0, sticky=EW)
        self.layers.append(LayerBase(canvas))
        self.layers.append(LayerEntities(canvas))
        self.layers.append(LayerAlienBBox(canvas))
        self.layers.append(LayerLabels(canvas))

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
    name = None
    enabled = None
    canvas = None
    callback = None
    game_state = None
    width = 0
    height = 0

    def __init__(self, canvas, name, enabled=True):
        self.enabled = BooleanVar(canvas)
        self.enabled.set(enabled)
        self.canvas = canvas
        self.name = name
        self.width = ai.entelect.MAP_WIDTH * RENDER_SCALE_FACTOR
        self.height = ai.entelect.MAP_HEIGHT * RENDER_SCALE_FACTOR

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

    def __init__(self, canvas):
        Layer.__init__(self, canvas, 'Base')
        canvas.create_line(0, 0, self.width, self.height)
        canvas.create_line(0, self.height, self.width, 0)

    # reload canvas with new game state
    def render_cell(self, canvas, cell, column_index, row_index, left, top, right, bottom):
        rect = canvas.create_rectangle(left, top, right, bottom, state=DISABLED)
        if not cell:
            canvas.itemconfig(rect, fill='lightgrey')
            return
        if cell['Type'] == ai.entelect.WALL:
            canvas.itemconfig(rect, fill='grey')


# entities layer
class LayerEntities(LayerCellBase):

    def __init__(self, canvas):
        Layer.__init__(self, canvas, 'Entities')

    def render_cell(self, canvas, cell, column_index, row_index, left, top, right, bottom):
        if not cell:
            return

        player_number = cell['PlayerNumber']
        if not player_number > 0:
            return

        rect = canvas.create_rectangle(left, top, right, bottom, activewidth=2)
        canvas.tag_bind(rect, '<ButtonPress-1>', lambda event, row=row_index, column=column_index: ai.event.dispatch(ai.event.Event('cell_clicked', {'row': row, 'column': column})))
        if cell['PlayerNumber'] == 1:
            canvas.itemconfig(rect, fill='blue')
        elif cell['PlayerNumber'] == 2:
            canvas.itemconfig(rect, fill='red')

# frame to labels
class LayerLabels(LayerCellBase):
    def __init__(self, canvas):
        Layer.__init__(self, canvas, 'Labels')

    def render_cell(self, canvas, cell, column_index, row_index, left, top, right, bottom):
        symbol = ai.entelect.cell_to_symbol(cell)
        canvas.create_text(left + RENDER_SCALE_FACTOR / 2, top + RENDER_SCALE_FACTOR / 2, text=symbol, state=DISABLED)

# draw bounding box around aliens
class LayerAlienBBox(Layer):

    def __init__(self, canvas):
        Layer.__init__(self, canvas, 'Alien BBox')

    def render(self, canvas):
        blackboard = Blackboard()
        blackboard.set('game_state', self.game_state)
        ai.expert.field_analyst.run(blackboard)
        bbox = blackboard.get('your_alien_bbox')
        canvas.create_rectangle(bbox['left'] * RENDER_SCALE_FACTOR, bbox['top'] * RENDER_SCALE_FACTOR, (bbox['right'] + 1) * RENDER_SCALE_FACTOR, (bbox['bottom'] + 1) * RENDER_SCALE_FACTOR, outline='blue', width=2, state=DISABLED)
        bbox = blackboard.get('enemy_alien_bbox')
        canvas.create_rectangle(bbox['left'] * RENDER_SCALE_FACTOR, bbox['top'] * RENDER_SCALE_FACTOR, (bbox['right'] + 1) * RENDER_SCALE_FACTOR, (bbox['bottom'] + 1) * RENDER_SCALE_FACTOR, outline='red', width=2, state=DISABLED)


# boostrap application
root = Tk()
root.resizable(0,0)
app = Application(master=root)
root.mainloop()
