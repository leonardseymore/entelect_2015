from Tkinter import *
import tkFileDialog
import ai.io
import ai.entelect
from ui.widgets import KeyValueGrid


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

    def __init__(self, master=None):
        Frame.__init__(self, master)
        master.wm_title('Entelect 2015 UI Toolkit')
        master.iconbitmap('resources/invader.ico')
        self.create_widgets()

    # file dialog to load game state file
    def open_state_file(self):
        filename = tkFileDialog.askopenfilename(filetypes=[("State files", "state.json")])
        if filename:
            self.game_state_file = filename
            self.game_state = ai.io.load_state(filename)
            self.game_cells_frame.load_game_state(self.game_state)

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
            window.config(width=400)
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

        self.game_cells_frame = GameCellsFrame(frame, CellDecorator(), self.cell_selected_handler)
        self.game_cells_frame.grid(row=0, rowspan=2, sticky=W)

# modify cells
class CellDecorator():
    def __init__(self):
        return

    # custom background rendering logic
    def update_rect(self, game_state, cell, canvas, rect):
        if not cell:
            canvas.itemconfig(rect, fill='lightgrey')
            return

        if cell['Type'] == ai.entelect.WALL:
            canvas.itemconfig(rect, fill='grey')

        if cell['PlayerNumber'] == 1:
            canvas.itemconfig(rect, fill='blue')

        if cell['PlayerNumber'] == 2:
            canvas.itemconfig(rect, fill='red')

    # custom label rendering logic
    def update_text(self, game_state, cell, canvas, text):
        return

# frame to render game cells
class GameCellsFrame(Canvas):
    callback = None
    game_state = None
    cell_modifier = None

    def __init__(self, master, cell_modifier, callback):
        Canvas.__init__(self, master, width=ai.entelect.MAP_WIDTH * RENDER_SCALE_FACTOR, height=ai.entelect.MAP_HEIGHT * RENDER_SCALE_FACTOR, bd=1, relief=SUNKEN)
        self.cell_modifier = cell_modifier
        self.callback = callback
        self.bind('<ButtonPress-1>', self.button_click)
        self.create_line(0, 0, ai.entelect.MAP_WIDTH * RENDER_SCALE_FACTOR, ai.entelect.MAP_HEIGHT * RENDER_SCALE_FACTOR)
        self.create_line(0, ai.entelect.MAP_HEIGHT * RENDER_SCALE_FACTOR, ai.entelect.MAP_WIDTH * RENDER_SCALE_FACTOR, 0)

    # handler when cell is clicked
    def button_click(self, event):
        if not self.game_state:
            return
        column = event.x / RENDER_SCALE_FACTOR
        row = event.y / RENDER_SCALE_FACTOR
        self.callback(self.game_state['Map']['Rows'][row][column])

    # reload canvas with new game state
    def load_game_state(self, game_state):
        self.delete(ALL)
        self.game_state = game_state
        game_map = game_state['Map']
        for row_index, row in enumerate(game_map['Rows']):
            for column_index, cell in enumerate(row):
                symbol = ai.entelect.cell_to_symbol(cell)
                rect = self.create_rectangle(column_index * RENDER_SCALE_FACTOR, row_index * RENDER_SCALE_FACTOR, column_index * RENDER_SCALE_FACTOR + RENDER_SCALE_FACTOR, row_index * RENDER_SCALE_FACTOR + RENDER_SCALE_FACTOR, activewidth=2)
                self.cell_modifier.update_rect(game_state, cell, self, rect)
                text = self.create_text(column_index * RENDER_SCALE_FACTOR + RENDER_SCALE_FACTOR / 2, row_index * RENDER_SCALE_FACTOR + RENDER_SCALE_FACTOR / 2, text=symbol, state=DISABLED)
                self.cell_modifier.update_text(game_state, cell, self, text)

# boostrap application
root = Tk()
app = Application(master=root)
root.mainloop()
