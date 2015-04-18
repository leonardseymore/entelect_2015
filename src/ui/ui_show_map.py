from Tkinter import *
import tkFileDialog
import ai.io
import ai.entelect


class Application(Frame):
    game_cells_frame = None
    game_info_frame = None
    cell_info_frame = None

    def __init__(self, master=None):
        Frame.__init__(self, master)
        master.wm_title('Entelect 2015 UI Toolkit')
        master.iconbitmap('resources/invader.ico')
        master.geometry("640x480")
        self.create_widgets()

    def open_state_file(self):
        filename = tkFileDialog.askopenfilename(filetypes=[("State files", "state.json")])
        if filename:
            game_state = ai.io.load_state(filename)
            self.game_cells_frame.load_game_state(game_state)
            self.game_info_frame.load_game_state(game_state)

    def cell_selected_handler(self, cell):
        self.cell_info_frame.load_cell_state(cell)

    def create_widgets(self):
        menu = Menu(self.master)
        file_menu = Menu(menu, tearoff=0)
        file_menu.add_command(label="Load State File", command=self.open_state_file)
        file_menu.add_command(label="Exit", command=self.master.quit)
        menu.add_cascade(label='File', menu=file_menu)
        self.master.config(menu=menu)

        self.game_cells_frame = GameCellsFrame(self.master, self.cell_selected_handler)
        self.game_cells_frame.grid(row=0, rowspan=2, sticky=NSEW)
        self.game_info_frame = GameInfoFrame(self.master)
        self.game_info_frame.grid(row=0, column=1, sticky=NSEW)
        self.cell_info_frame = CellInfoFrame(self.master)
        self.cell_info_frame.grid(row=1, column=1, sticky=NSEW)


class GameCellsFrame(Frame):
    callback = None
    labels = [[0 for x in range(19)] for x in range(25)]
    game_state = None

    def __init__(self, master, callback):
        Frame.__init__(self, master, bd=1, relief=SUNKEN)
        self.callback = callback
        self.create_widgets()

    def button_click(self, row, column):
        if not self.game_state:
            return
        self.callback(self.game_state['Map']['Rows'][row][column])

    def create_widgets(self):
        for row_index in range(0, 25):
            for column_index in range(19):
                label_var = StringVar()
                self.labels[row_index][column_index] = label_var
                button = Button(self, width=1, textvariable=label_var, command=lambda row=row_index, column=column_index: self.button_click(row, column))
                button.grid(sticky=NSEW, row=row_index, column=column_index)

    def load_game_state(self, game_state):
        self.game_state = game_state
        game_map = game_state['Map']
        for row_index, row in enumerate(game_map['Rows']):
            for column_index, cell in enumerate(row):
                symbol = ai.entelect.cell_to_symbol(cell)
                self.labels[row_index][column_index].set(symbol)


class GameInfoFrame(Frame):
    def __init__(self, master):
        Frame.__init__(self, master, bd=1, relief=SUNKEN)
        Label(self, text="Game Info", font="Helvetica 16 bold italic").grid(columnspan=2)

    def load_game_state(self, game_state):
        Label(self, text="Player 1:").grid(row=1)
        Label(self, text=game_state['Players'][0]['PlayerName']).grid(row=1, column=2)


class CellInfoFrame(Frame):
    labels = {}

    def __init__(self, master):
        Frame.__init__(self, master, bd=1, relief=SUNKEN)
        self.create_widgets()

    def create_widgets(self):
        Label(self, text="Cell Info", font="Helvetica 16 bold italic").grid(columnspan=2, sticky=W)

        for idx, label in enumerate(['Id', 'Alive', 'X', 'Y', 'Width', 'Height', 'Type', 'PlayerNumber', 'Command', 'CommandFeedback', 'LivesCost']):
            Label(self, text=label + ': ').grid(row=idx + 1, sticky=E)
            label_var = StringVar()
            self.labels[label] = label_var
            Label(self, textvariable=label_var).grid(row=idx + 1, column=1, sticky=W)

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

root = Tk()
app = Application(master=root)
root.mainloop()
