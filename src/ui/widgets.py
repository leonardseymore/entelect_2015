from Tkinter import *
import ai.expert

class KeyValueGrid(Frame):

    visible = False
    frame = None

    def __init__(self, master):
        Frame.__init__(self, master, bd=1, relief=SUNKEN)

    # creates a new grid from the supplied object into its own frame
    def load(self, obj):
        frame = Frame(self)
        self.frame = frame
        self.visible = True
        frame.grid(columnspan=2, sticky=NSEW)

        if type(obj).__name__ == 'instance':
            obj = obj.get_obj()

        rowspan = 1
        if isinstance(obj, dict):
            row = 0
            for key in obj:
                value = obj[key]
                child_grid = KeyValueGrid(frame)
                child_rowspan = child_grid.load(value)
                child_grid.grid(row=row, column=1, sticky=W)
                label = Label(frame, text='%s :' % key)
                label.grid(rowspan=child_rowspan, row=row, sticky=NE)
                label.bind("<Button-1>", lambda e, row_label=label, row_index=row, row_label_span=child_rowspan, toggle_grid=child_grid: toggle_grid.toggle_visibility(row_index, row_label, row_label_span))
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

    def load_subframe(self, parent, obj):
        for row, item in enumerate(obj):
            list_frame = Frame(parent)
            list_frame.grid(columnspan=2, sticky=NSEW)
            child_grid = KeyValueGrid(list_frame)
            child_grid.load(item)
            child_grid.grid(row=row, column=1, sticky=W)

    def toggle_visibility(self, row, row_label, row_label_span):
        self.visible = not self.visible
        if self.visible:
            row_label.grid(rowspan=row_label_span, row=row, sticky=NE)
            self.grid(row=row, column=1, sticky=W)
        else:
            row_label.grid(rowspan=1, row=row, sticky=NE)
            self.grid_forget()

    # handler called when clicking on a cell
class KeyValueWindow():
    menu = None
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
            self.build_window()

    def build_window(self):
        self.window = Toplevel(self.parent)
        self.window.bind('<Control-r>', lambda event: self.reload())
        self.window.geometry(self.geometry)
        self.window.title(self.title)
        self.window.iconbitmap('resources/invader.ico')

        menu = Menu(self.window)
        self.menu = menu

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

class BlackboardWindow(KeyValueWindow):
    def build_window(self):
        KeyValueWindow.build_window(self)
        menu = self.menu
        experts_menu = Menu(menu, tearoff=0)
        for expert in ai.expert.experts:
            experts_menu.add_command(label=expert.name, command=lambda expert_to_run=expert: self.run_expert(expert_to_run))
        menu.add_cascade(label='Run Expert', menu=experts_menu)

    def run_expert(self, expert):
        expert.run(self.get_value())
        self.reload()

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
