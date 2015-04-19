from Tkinter import *
import tkFileDialog
import ai.io
import ai.entelect
from ui.widgets import KeyValueGrid
from os.path import dirname
from os.path import join
from os.path import exists

# scale up the renderer
RENDER_SCALE_FACTOR = 20


# GUI application
class Application(Frame):
    game_state_file = None
    game_state = None

    game_cells_frame = None
    game_info_window = None
    game_info_grid = None
    cell_info_window = None
    cell_info_grid = None

    labels = {}
    layers = []
    canvas = None

    def __init__(self, master=None):
        Frame.__init__(self, master)
        master.wm_title('Entelect 2015 UI Toolkit')
        master.iconbitmap('resources/invader.ico')
        self.labels['RoundNumber'] = StringVar()
        self.create_widgets()

    # file dialog to load game state file
    def open_state_file(self):
        filename = tkFileDialog.askopenfilename(filetypes=[("State files", "state.json")])
        if filename:
            self.load_state_file(filename)

    # file dialog to load game state file
    def load_state_file(self, filename):
        self.game_state_file = filename
        self.game_state = ai.io.load_state(filename)
        self.canvas.delete(ALL)
        for layer in self.layers:
            layer.load_game_state(self.game_state)
        self.labels['RoundNumber'].set('Round: %d/%d' % (self.game_state['RoundNumber'], self.game_state['RoundLimit']))

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
        if not self.game_state :
            return
        round_number = self.game_state['RoundNumber']
        self.load_specific_state(round_number - 1)

    # tries to load the next state
    def load_next_state(self):
        if not self.game_state:
            return
        round_number = self.game_state['RoundNumber']
        self.load_specific_state(round_number + 1)

    # show game info window
    def open_game_info_window(self):
        window = self.game_info_window
        if not window or not window.winfo_exists():
            window = Toplevel()
            self.game_info_window = window
            window.title("Game Information")
            window.iconbitmap('resources/invader.ico')

        grid = self.game_info_grid
        if grid:
            grid.destroy()

        self.game_info_grid = KeyValueGrid(window)
        grid = self.game_info_grid
        grid.load(self.game_state)
        grid.grid(sticky=NSEW)

    # handler called when clicking on a cell
    def cell_selected_handler(self, cell):
        window = self.cell_info_window
        if not window or not window.winfo_exists():
            window = Toplevel()
            window.geometry('400x300')
            self.cell_info_window = window
            window.title("Cell Information")
            window.iconbitmap('resources/invader.ico')

        grid = self.cell_info_grid
        if grid:
            grid.destroy()
        print cell
        self.cell_info_grid = KeyValueGrid(window)
        grid = self.cell_info_grid
        grid.load(cell)
        grid.grid(sticky=NSEW)

    # initialize application widgets
    def create_widgets(self):
        menu = Menu(self.master)

        file_menu = Menu(menu, tearoff=0)
        file_menu.add_command(label="Load State File", command=self.open_state_file)
        file_menu.add_command(label="Exit", command=self.master.quit)
        menu.add_cascade(label='File', menu=file_menu)

        state_menu = Menu(menu, tearoff=0)
        state_menu.add_command(label="Show Game Info", command=self.open_game_info_window)
        menu.add_cascade(label='State', menu=state_menu)

        self.master.config(menu=menu)

        frame = Frame(self.master)
        frame.grid(sticky=NSEW)

        canvas = Canvas(frame, width=ai.entelect.MAP_WIDTH * RENDER_SCALE_FACTOR, height=ai.entelect.MAP_HEIGHT * RENDER_SCALE_FACTOR, bd=1, relief=SUNKEN)
        self.canvas = canvas
        canvas.grid(row=0, sticky=EW)
        layer_base = LayerBase(canvas, self.cell_selected_handler)
        self.layers.append(layer_base)
        layer_labels = LayerLabels(canvas)
        self.layers.append(layer_labels)

        nav_frame = Frame(frame)
        nav_frame.grid(sticky=EW, row=1)
        Button(nav_frame, text='<', command=self.load_prev_state).grid(row=0, sticky=W)
        Button(nav_frame, text='>', command=self.load_next_state).grid(row=0, column=1, sticky=E)
        Label(nav_frame, textvariable=self.labels['RoundNumber']).grid(row=0, column=2, sticky=W)
        self.master.bind('<Left>', lambda event: self.load_prev_state())
        self.master.bind('<Right>', lambda event: self.load_next_state())

# frame to render on a canvas layer
class Layer():
    canvas = None
    callback = None
    game_state = None
    width = 0
    height = 0

    def __init__(self, canvas):
        self.canvas = canvas
        self.width = ai.entelect.MAP_WIDTH * RENDER_SCALE_FACTOR
        self.height = ai.entelect.MAP_HEIGHT * RENDER_SCALE_FACTOR

    # reload canvas with new game state
    def load_game_state(self, game_state):
        self.game_state = game_state
        game_map = game_state['Map']
        for row_index, row in enumerate(game_map['Rows']):
            for column_index, cell in enumerate(row):
                self.render_cell(self.canvas, cell, column_index, row_index, column_index * RENDER_SCALE_FACTOR, row_index * RENDER_SCALE_FACTOR, column_index * RENDER_SCALE_FACTOR + RENDER_SCALE_FACTOR, row_index * RENDER_SCALE_FACTOR + RENDER_SCALE_FACTOR)

    # base class to implement layer specific
    def render_cell(self, canvas, cell, column_index, row_index, left, top, right, bottom):
        return

# frame to render game cells
class LayerBase(Layer):
    callback = None

    def __init__(self, canvas, callback):
        Layer.__init__(self, canvas)
        self.callback = callback
        canvas.create_line(0, 0, self.width, self.height)
        canvas.create_line(0, self.height, self.width, 0)

    # reload canvas with new game state
    def render_cell(self, canvas, cell, column_index, row_index, left, top, right, bottom):
        rect = canvas.create_rectangle(left, top, right, bottom, activewidth=2)
        canvas.tag_bind(rect, '<ButtonPress-1>', lambda event, row=row_index, column=column_index:self.callback(self.game_state['Map']['Rows'][row][column]))
        if not cell:
            canvas.itemconfig(rect, fill='lightgrey')
            return
        if cell['Type'] == ai.entelect.WALL:
            canvas.itemconfig(rect, fill='grey')
        if cell['PlayerNumber'] == 1:
            canvas.itemconfig(rect, fill='blue')
        if cell['PlayerNumber'] == 2:
            canvas.itemconfig(rect, fill='red')

# frame to labels
class LayerLabels(Layer):
    def render_cell(self, canvas, cell, column_index, row_index, left, top, right, bottom):
        symbol = ai.entelect.cell_to_symbol(cell)
        canvas.create_text(left + RENDER_SCALE_FACTOR / 2, top + RENDER_SCALE_FACTOR / 2, text=symbol, state=DISABLED)

# boostrap application
root = Tk()
app = Application(master=root)
root.mainloop()
