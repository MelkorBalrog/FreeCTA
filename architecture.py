import tkinter as tk
from tkinter import ttk


class SysMLDiagramWindow(tk.Toplevel):
    """Base window with a simple canvas and toolbox."""

    def __init__(self, master, title, tools):
        super().__init__(master)
        self.title(title)
        self.geometry("800x600")
        self.current_tool = None
        self.start = None

        self.toolbox = ttk.Frame(self)
        self.toolbox.pack(side=tk.LEFT, fill=tk.Y)

        for tool in tools:
            ttk.Button(self.toolbox, text=tool,
                       command=lambda t=tool: self.select_tool(t)).pack(
                fill=tk.X, padx=2, pady=2)

        self.canvas = tk.Canvas(self, bg="white")
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    def select_tool(self, tool):
        self.current_tool = tool
        self.start = None

    def on_canvas_click(self, event):
        c = self.canvas
        x, y = event.x, event.y
        t = self.current_tool
        if not t:
            return
        if t == "Actor":
            c.create_oval(x-10, y-30, x+10, y-10)
            c.create_line(x, y-10, x, y+20)
            c.create_line(x-15, y, x+15, y)
            c.create_line(x, y+20, x-10, y+40)
            c.create_line(x, y+20, x+10, y+40)
        elif t == "Use Case":
            c.create_oval(x-40, y-20, x+40, y+20)
        elif t == "System Boundary":
            c.create_rectangle(x-100, y-60, x+100, y+60, dash=(4, 2))
        elif t in ("Association", "Include", "Extend", "Flow", "Connector"):
            if self.start is None:
                self.start = (x, y)
            else:
                dash = ()
                if t in ("Include", "Extend"):
                    dash = (4, 2)
                    text = "<<include>>" if t == "Include" else "<<extend>>"
                    c.create_text((self.start[0] + x)/2,
                                   (self.start[1] + y)/2,
                                   text=text, anchor="center")
                c.create_line(self.start[0], self.start[1], x, y,
                               arrow=tk.LAST, dash=dash)
                self.start = None
        else:
            c.create_rectangle(x-30, y-20, x+30, y+20)


class UseCaseDiagramWindow(SysMLDiagramWindow):
    def __init__(self, master):
        tools = [
            "Actor",
            "Use Case",
            "System Boundary",
            "Association",
            "Include",
            "Extend",
        ]
        super().__init__(master, "Use Case Diagram", tools)


class ActivityDiagramWindow(SysMLDiagramWindow):
    def __init__(self, master):
        tools = [
            "Action",
            "Initial",
            "Final",
            "Decision",
            "Merge",
            "Fork",
            "Join",
            "Flow",
        ]
        super().__init__(master, "Activity Diagram", tools)

    def on_canvas_click(self, event):
        c = self.canvas
        x, y = event.x, event.y
        t = self.current_tool
        if not t:
            return
        if t == "Action":
            c.create_rectangle(x-40, y-20, x+40, y+20)
        elif t == "Initial":
            c.create_oval(x-10, y-10, x+10, y+10, fill="black")
        elif t == "Final":
            c.create_oval(x-15, y-15, x+15, y+15)
            c.create_oval(x-10, y-10, x+10, y+10, fill="black")
        elif t in ("Decision", "Merge"):
            c.create_polygon(x, y-20, x+20, y, x, y+20, x-20, y,
                             fill="white", outline="black")
        elif t in ("Fork", "Join"):
            c.create_rectangle(x-30, y-5, x+30, y+5, fill="black")
        elif t == "Flow":
            if self.start is None:
                self.start = (x, y)
            else:
                c.create_line(self.start[0], self.start[1], x, y, arrow=tk.LAST)
                self.start = None
        else:
            super().on_canvas_click(event)


class BlockDiagramWindow(SysMLDiagramWindow):
    def __init__(self, master):
        tools = [
            "Block",
            "Association",
        ]
        super().__init__(master, "Block Diagram", tools)

    def on_canvas_click(self, event):
        c = self.canvas
        x, y = event.x, event.y
        t = self.current_tool
        if not t:
            return
        if t == "Block":
            c.create_rectangle(x-60, y-40, x+60, y+40)
        elif t == "Association":
            if self.start is None:
                self.start = (x, y)
            else:
                c.create_line(self.start[0], self.start[1], x, y, arrow=tk.LAST)
                self.start = None
        else:
            super().on_canvas_click(event)


class InternalBlockDiagramWindow(SysMLDiagramWindow):
    def __init__(self, master):
        tools = [
            "Block",
            "Part",
            "Port",
            "Connector",
        ]
        super().__init__(master, "Internal Block Diagram", tools)

    def on_canvas_click(self, event):
        c = self.canvas
        x, y = event.x, event.y
        t = self.current_tool
        if not t:
            return
        if t == "Block":
            c.create_rectangle(x-60, y-40, x+60, y+40)
        elif t == "Part":
            c.create_rectangle(x-40, y-30, x+40, y+30, dash=(4, 2))
        elif t == "Port":
            c.create_rectangle(x-10, y-10, x+10, y+10, fill="black")
        elif t == "Connector":
            if self.start is None:
                self.start = (x, y)
            else:
                c.create_line(self.start[0], self.start[1], x, y, arrow=tk.LAST)
                self.start = None
        else:
            super().on_canvas_click(event)
