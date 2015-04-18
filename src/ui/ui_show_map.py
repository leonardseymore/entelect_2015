from Tkinter import *
import tkFileDialog
import ai.io
import ai.entelect


# scale up the renderer
RENDER_SCALE_FACTOR = 20


# GUI application
class Application(Frame):
    game_cells_frame = None
    game_info_frame = None
    cell_info_frame = None

    def __init__(self, master=None):
        Frame.__init__(self, master)
        master.wm_title('Entelect 2015 UI Toolkit')
        master.iconbitmap('resources/invader.ico')
        master.geometry("640x640")
        self.create_widgets()

    # file dialog to load game state file
    def open_state_file(self):
        filename = tkFileDialog.askopenfilename(filetypes=[("State files", "state.json")])
        if filename:
            game_state = ai.io.load_state(filename)
            self.game_info_frame.load_game_state(game_state)
            self.game_cells_frame.load_game_state(game_state)

    # handler called when clicking on a cell
    def cell_selected_handler(self, cell):
        self.cell_info_frame.load_cell_state(cell)

    # initialize application widgets
    def create_widgets(self):
        menu = Menu(self.master)
        file_menu = Menu(menu, tearoff=0)
        file_menu.add_command(label="Load State File", command=self.open_state_file)
        file_menu.add_command(label="Exit", command=self.master.quit)
        menu.add_cascade(label='File', menu=file_menu)
        self.master.config(menu=menu)

        self.game_cells_frame = GameCellsFrame(self.master, CellDecorator(), self.cell_selected_handler)
        self.game_cells_frame.grid(row=0, rowspan=2, sticky=NSEW)
        self.game_info_frame = GameInfoFrame(self.master)
        self.game_info_frame.grid(row=0, column=1, sticky=NSEW)
        self.cell_info_frame = CellInfoFrame(self.master)
        self.cell_info_frame.grid(row=1, column=1, sticky=NSEW)

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
        print (row, column)
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

# show game details
class GameInfoFrame(Frame):
    labels = {}
    game_state = None

    def __init__(self, master):
        Frame.__init__(self, master, bd=1, relief=SUNKEN)
        Label(self, text="Game Info", font="Helvetica 16 bold italic").grid(columnspan=2, sticky=W)
        self.create_widgets()

    # create label widgets
    def create_widgets(self):
        self.create_label('Rounds', 'Round:', 1)
        prev_next_frame = Frame(self)
        prev_next_frame.grid(columnspan=2, sticky=NSEW)
        Button(prev_next_frame, text='<').grid(row=0, column=0, sticky=W)
        Button(prev_next_frame, text='>').grid(row=0, column=1, sticky=E)

        Label(self, text="Player 1", font="Helvetica 12 bold").grid(row=3, columnspan=2, sticky=W)
        self.create_label('PlayerName1', 'Player 1:', 4)

        Label(self, text="Player 2", font="Helvetica 12 bold").grid(row=5, columnspan=2, sticky=W)
        self.create_label('PlayerName2', 'Player 2:', 6)

    # creates a new label
    def create_label(self, key, label, row):
        Label(self, text=label).grid(row=row, sticky=E)
        label_var = StringVar()
        self.labels[key] = label_var
        Label(self, textvariable=label_var).grid(row=row, column=1, sticky=W)

    # update labels with new game state info
    def load_game_state(self, game_state):
        self.labels['Rounds'].set(str(game_state['RoundNumber']) + '/' + str(game_state['RoundLimit']))

        player1 = game_state['Players'][0]
        player2 = game_state['Players'][1]
        self.labels['PlayerName1'].set(player1['PlayerName'] + ' (' + str(player1['PlayerNumber']) + ')')
        self.labels['PlayerName2'].set(player1['PlayerName'] + ' (' + str(player2['PlayerNumber']) + ')')


# displays info of selected cell
class CellInfoFrame(Frame):
    labels = {}

    def __init__(self, master):
        Frame.__init__(self, master, bd=1, relief=SUNKEN)
        self.create_widgets()

    # initialize widgets
    def create_widgets(self):
        Label(self, text="Cell Info", font="Helvetica 16 bold italic").grid(columnspan=2, sticky=W)

        for idx, label in enumerate(['Id', 'Alive', 'X', 'Y', 'Width', 'Height', 'Type', 'PlayerNumber', 'Command', 'CommandFeedback', 'LivesCost']):
            Label(self, text=label + ': ').grid(row=idx + 1, sticky=E)
            label_var = StringVar()
            self.labels[label] = label_var
            Label(self, textvariable=label_var).grid(row=idx + 1, column=1, sticky=W)

    # update labels with new cell info
    def load_cell_state(self, cell):
        if not cell:
            for key in self.labels:
                self.labels[key].set('')
            return

        for key in cell:
            self.labels[key].set(cell[key])

        if not cell.has_key('Command'):
            self.labels['Command'].set('')
            self.labels['CommandFeedback'].set('')
            self.labels['LivesCost'].set('')

# boostrap application
root = Tk()
app = Application(master=root)
root.mainloop()
