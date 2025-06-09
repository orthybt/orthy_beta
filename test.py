import tkinter as tk

# Component registry
components = {}

# --- Core GUI Elements ---

class Window:
    def __init__(self, name="main", title="My App"):
        self.name = name
        self.widget = tk.Tk()
        self.widget.title(title)
        components[name] = self

    def show(self):
        self.widget.mainloop()


class Frame:
    def __init__(self, name, parent="main", layout="pack"):
        self.name = name
        self.layout = layout
        self.parent = components[parent].widget
        self.widget = tk.Frame(self.parent, bg='red', highlightthickness=0)
        components[name] = self

    def show(self, **kwargs):
        if self.layout == "pack":
            self.widget.pack(**kwargs)
        elif self.layout == "grid":
            self.widget.grid(**kwargs)
        return self


class Label:
    def __init__(self, name, text=""):
        self.name = name
        self.text = text
        self.widget = None
        components[name] = self

    def inside(self, parent_name):
        parent = components[parent_name]
        self.widget = tk.Label(parent.widget, text=self.text, bg=None)
        self.parent = parent
        return self

    def show(self, **kwargs):
        if self.parent.layout == "pack":
            self.widget.pack(**kwargs)
        elif self.parent.layout == "grid":
            self.widget.grid(**kwargs)
        return self


class Button:
    def __init__(self, name, text="", command=None):
        self.name = name
        self.text = text
        self.command = command
        self.widget = None
        components[name] = self

    def inside(self, parent_name):
        parent = components[parent_name]
        self.widget = tk.Button(parent.widget, text=self.text, command=self.command)
        self.parent = parent
        return self

    def on_click(self, func):
        self.command = func
        if self.widget:
            self.widget.config(command=func)
        return self

    def show(self, **kwargs):
        if self.parent.layout == "pack":
            self.widget.pack(**kwargs)
        elif self.parent.layout == "grid":
            self.widget.grid(**kwargs)
        return self


class Input:
    def __init__(self, name):
        self.name = name
        self.var = tk.StringVar()
        self.widget = None
        components[name] = self

    def inside(self, parent_name):
        parent = components[parent_name]
        self.widget = tk.Entry(parent.widget, textvariable=self.var)
        self.parent = parent
        return self

    def show(self, **kwargs):
        if self.parent.layout == "pack":
            self.widget.pack(**kwargs)
        elif self.parent.layout == "grid":
            self.widget.grid(**kwargs)
        return self

    def get_value(self):
        return self.var.get()

    def set_value(self, value):
        self.var.set(value)
        return self


Window.show
Frame.show