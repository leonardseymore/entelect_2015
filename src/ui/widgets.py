from Tkinter import *


class KeyValueGrid(Frame):

    def __init__(self, master):
        Frame.__init__(self, master, bd=1, relief=SUNKEN)

    # creates a new grid from the supplied object into its own frame
    def load(self, obj):
        frame = Frame(self)
        frame.grid(columnspan=2, sticky=NSEW)

        rowspan = 1
        if isinstance(obj, dict):
            row = 0
            for key in obj:
                value = obj[key]
                child_grid = KeyValueGrid(frame)
                child_rowspan = child_grid.load(value)
                child_grid.grid(row=row, column=1, sticky=W)
                Label(frame, text='%s :' % key).grid(rowspan=child_rowspan, row=row, sticky=NE)
                row += 1
            rowspan = row
        elif isinstance(obj, list):
            if len(obj) > 0:
                ListExpandControl(frame, obj)
        else:
            display_value = 'Unsupported %s' % type(obj)
            if isinstance(obj, int) or isinstance(obj, unicode):
                display_value = str(obj)
            if obj:
                Label(frame, text=display_value).grid(columnspan=2, sticky=NSEW)

        return rowspan

    def load_subframe(self, parent, obj, row):
        row = 0
        for item in obj:
            list_frame = Frame(parent)
            list_frame.grid(columnspan=2, sticky=NSEW)
            child_grid = KeyValueGrid(list_frame)
            child_rowspan = child_grid.load(item)
            child_grid.grid(row=row, column=1, sticky=W)
            row += 1

    # handler called when clicking on a cell
class KeyValueWindow():
    parent = None
    title = None
    get_value = None
    geometry = None
    window = None
    grid = None

    def __init__(self, parent, title, get_value, geometry=None):
        self.parent = parent
        self.title = title
        self.geometry = geometry
        self.get_value = get_value

    def validate_window(self):
        if not self.window or not self.window.winfo_exists():
            self.window = Toplevel(self.parent)
            self.window.bind('<Control-r>', lambda event: self.reload())
            self.window.geometry(self.geometry)
            self.window.title(self.title)
            self.window.iconbitmap('resources/invader.ico')

            menu = Menu(self.window)

            object_menu = Menu(menu, tearoff=0)
            object_menu.add_command(label="Reload", command=self.reload)
            menu.add_cascade(label='Object', menu=object_menu)

            self.window.config(menu=menu)

    def show(self, obj):
        self.validate_window()

        if self.grid:
            self.grid.destroy()

        self.grid = KeyValueGrid(self.window)
        self.grid.load(obj)
        self.grid.grid(sticky=NSEW)

    def reload(self):
        if self.window and self.window.winfo_exists():
            self.show(self.get_value())

class ListExpandControl(Frame):
    master = None
    obj = None
    toggled_on = False
    child_frame = None
    toggle_button = None

    def __init__(self, master, obj):
        self.master = master
        self.obj = obj
        self.toggle_button = Button(master, text='> %d' % len(obj), command=self.toggle)
        self.toggle_button.grid(columnspan=2, sticky=NSEW)

    def toggle(self):
        self.toggled_on = not self.toggled_on
        self.toggle_button.config(text='%s %d' % ('V' if self.toggled_on else '>', len(self.obj)))

        if self.child_frame:
            self.child_frame.destroy()

        self.child_frame = Frame(self.master)
        self.child_frame.grid(columnspan=2, sticky=NSEW)

        if self.toggled_on:
            row = 0
            for item in self.obj:
                list_frame = Frame(self.child_frame)
                list_frame.grid(columnspan=2, sticky=NSEW)
                self.child_grid = KeyValueGrid(list_frame)
                self.child_grid.load(item)
                self.child_grid.grid(row=row, column=1, sticky=W)
                row += 1
