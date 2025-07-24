import tkinter as tk
from tkinter import ttk, simpledialog
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from sysml_spec import SYSML_PROPERTIES


_next_obj_id = 1


def _get_next_id() -> int:
    global _next_obj_id
    val = _next_obj_id
    _next_obj_id += 1
    return val


@dataclass
class SysMLObject:
    obj_id: int
    obj_type: str
    x: float
    y: float
    width: float = 80.0
    height: float = 40.0
    properties: Dict[str, str] = field(default_factory=dict)


class SysMLDiagramWindow(tk.Toplevel):
    """Base window for simple SysML diagrams with zoom and pan support."""

    def __init__(self, master, title, tools):
        super().__init__(master)
        self.title(title)
        self.geometry("800x600")

        self.zoom = 1.0
        self.current_tool = None
        self.start = None
        self.objects: List[SysMLObject] = []
        self.connections: List[Tuple[int, int, str]] = []
        self.selected_obj: SysMLObject | None = None
        self.drag_offset = (0, 0)

        self.toolbox = ttk.Frame(self)
        self.toolbox.pack(side=tk.LEFT, fill=tk.Y)

        # Always provide a select tool
        tools = ["Select"] + tools
        for tool in tools:
            ttk.Button(self.toolbox, text=tool,
                       command=lambda t=tool: self.select_tool(t)).pack(
                fill=tk.X, padx=2, pady=2)

        self.canvas = tk.Canvas(self, bg="white")
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.canvas.bind("<Button-1>", self.on_left_press)
        self.canvas.bind("<B1-Motion>", self.on_left_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_release)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<ButtonPress-3>", self.on_rc_press)
        self.canvas.bind("<B3-Motion>", self.on_rc_drag)
        self.canvas.bind("<Control-MouseWheel>", self.on_ctrl_mousewheel)

        self.redraw()

    def select_tool(self, tool):
        self.current_tool = tool
        self.start = None

    # ------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------
    def on_left_press(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        obj = self.find_object(x, y)
        t = self.current_tool

        if t in ("Association", "Include", "Extend", "Flow", "Connector"):
            if self.start is None:
                if obj:
                    self.start = obj
            else:
                if obj and obj != self.start:
                    self.connections.append((self.start.obj_id, obj.obj_id, t))
                self.start = None
                self.redraw()
        elif t and t != "Select":
            new_obj = SysMLObject(_get_next_id(), t, x / self.zoom, y / self.zoom)
            key = f"{t.replace(' ', '')}Usage"
            for prop in SYSML_PROPERTIES.get(key, []):
                new_obj.properties.setdefault(prop, "")
            self.objects.append(new_obj)
            self.redraw()
        else:
            if obj:
                self.selected_obj = obj
                self.drag_offset = (x / self.zoom - obj.x, y / self.zoom - obj.y)

    def on_left_drag(self, event):
        if not self.selected_obj:
            return
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.selected_obj.x = x / self.zoom - self.drag_offset[0]
        self.selected_obj.y = y / self.zoom - self.drag_offset[1]
        self.redraw()

    def on_left_release(self, _event):
        self.selected_obj = None

    def on_double_click(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        obj = self.find_object(x, y)
        if obj:
            SysMLObjectDialog(self, obj)
            self.redraw()

    def on_rc_press(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def on_rc_drag(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def on_ctrl_mousewheel(self, event):
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    # ------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------
    def find_object(self, x: float, y: float) -> SysMLObject | None:
        for obj in reversed(self.objects):
            ox = obj.x * self.zoom
            oy = obj.y * self.zoom
            w = obj.width * self.zoom / 2
            h = obj.height * self.zoom / 2
            if ox - w <= x <= ox + w and oy - h <= y <= oy + h:
                return obj
        return None

    def zoom_in(self):
        self.zoom *= 1.2
        self.redraw()

    def zoom_out(self):
        self.zoom /= 1.2
        self.redraw()

    def redraw(self):
        self.canvas.delete("all")
        for obj in self.objects:
            self.draw_object(obj)
        for a, b, _t in self.connections:
            src = self.get_object(a)
            dst = self.get_object(b)
            if src and dst:
                self.draw_connection(src, dst)
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def draw_object(self, obj: SysMLObject):
        x = obj.x * self.zoom
        y = obj.y * self.zoom
        w = obj.width * self.zoom / 2
        h = obj.height * self.zoom / 2
        if obj.obj_type == "Actor":
            self.canvas.create_oval(x - 10 * self.zoom, y - 30 * self.zoom,
                                    x + 10 * self.zoom, y - 10 * self.zoom)
            self.canvas.create_line(x, y - 10 * self.zoom, x, y + 20 * self.zoom)
            self.canvas.create_line(x - 15 * self.zoom, y, x + 15 * self.zoom, y)
            self.canvas.create_line(x, y + 20 * self.zoom,
                                    x - 10 * self.zoom, y + 40 * self.zoom)
            self.canvas.create_line(x, y + 20 * self.zoom,
                                    x + 10 * self.zoom, y + 40 * self.zoom)
        elif obj.obj_type == "Use Case":
            self.canvas.create_oval(x - w, y - h, x + w, y + h)
        elif obj.obj_type == "System Boundary":
            self.canvas.create_rectangle(x - 100 * self.zoom, y - 60 * self.zoom,
                                        x + 100 * self.zoom, y + 60 * self.zoom,
                                        dash=(4, 2))
        elif obj.obj_type in ("Action", "Block", "Part", "Port"):
            dash = ()
            fill = ""
            if obj.obj_type == "Part":
                dash = (4, 2)
            if obj.obj_type == "Port":
                fill = "black"
                self.canvas.create_rectangle(x - 10 * self.zoom, y - 10 * self.zoom,
                                            x + 10 * self.zoom, y + 10 * self.zoom,
                                            fill=fill)
            else:
                self.canvas.create_rectangle(x - w, y - h, x + w, y + h,
                                            dash=dash, fill=fill)
        elif obj.obj_type in ("Initial", "Final"):
            if obj.obj_type == "Initial":
                self.canvas.create_oval(x - 10 * self.zoom, y - 10 * self.zoom,
                                        x + 10 * self.zoom, y + 10 * self.zoom,
                                        fill="black")
            else:
                self.canvas.create_oval(x - 15 * self.zoom, y - 15 * self.zoom,
                                        x + 15 * self.zoom, y + 15 * self.zoom)
                self.canvas.create_oval(x - 10 * self.zoom, y - 10 * self.zoom,
                                        x + 10 * self.zoom, y + 10 * self.zoom,
                                        fill="black")
        elif obj.obj_type in ("Decision", "Merge"):
            self.canvas.create_polygon(x, y - 20 * self.zoom,
                                      x + 20 * self.zoom, y,
                                      x, y + 20 * self.zoom,
                                      x - 20 * self.zoom, y,
                                      fill="white", outline="black")
        elif obj.obj_type in ("Fork", "Join"):
            self.canvas.create_rectangle(x - 30 * self.zoom, y - 5 * self.zoom,
                                        x + 30 * self.zoom, y + 5 * self.zoom,
                                        fill="black")
        else:
            self.canvas.create_rectangle(x - w, y - h, x + w, y + h)

        label_lines = [obj.properties.get("name", obj.obj_type)]
        key = f"{obj.obj_type.replace(' ', '')}Usage"
        for prop in SYSML_PROPERTIES.get(key, []):
            val = obj.properties.get(prop)
            if val:
                label_lines.append(f"{prop}: {val}")
        self.canvas.create_text(x, y, text="\n".join(label_lines), anchor="center")

    def draw_connection(self, a: SysMLObject, b: SysMLObject):
        ax, ay = a.x * self.zoom, a.y * self.zoom
        bx, by = b.x * self.zoom, b.y * self.zoom
        self.canvas.create_line(ax, ay, bx, by, arrow=tk.LAST)

    def get_object(self, oid: int) -> SysMLObject | None:
        for o in self.objects:
            if o.obj_id == oid:
                return o
        return None

class SysMLObjectDialog(simpledialog.Dialog):
    """Simple dialog for editing SysML object properties."""

    def __init__(self, master, obj: SysMLObject):
        self.obj = obj
        super().__init__(master, title=f"Edit {obj.obj_type}")

    def body(self, master):
        ttk.Label(master, text="Name:").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        self.name_var = tk.StringVar(value=self.obj.properties.get("name", ""))
        ttk.Entry(master, textvariable=self.name_var).grid(row=0, column=1, padx=4, pady=4)
        ttk.Label(master, text="Width:").grid(row=1, column=0, sticky="e", padx=4, pady=2)
        self.width_var = tk.StringVar(value=str(self.obj.width))
        ttk.Entry(master, textvariable=self.width_var).grid(row=1, column=1, padx=4, pady=2)
        ttk.Label(master, text="Height:").grid(row=2, column=0, sticky="e", padx=4, pady=2)
        self.height_var = tk.StringVar(value=str(self.obj.height))
        ttk.Entry(master, textvariable=self.height_var).grid(row=2, column=1, padx=4, pady=2)
        self.entries = {}
        row = 3
        key = f"{self.obj.obj_type.replace(' ', '')}Usage"
        for prop in SYSML_PROPERTIES.get(key, []):
            ttk.Label(master, text=f"{prop}:").grid(row=row, column=0, sticky="e", padx=4, pady=2)
            var = tk.StringVar(value=self.obj.properties.get(prop, ""))
            ttk.Entry(master, textvariable=var).grid(row=row, column=1, padx=4, pady=2)
            self.entries[prop] = var
            row += 1

    def apply(self):
        self.obj.properties["name"] = self.name_var.get()
        for prop, var in self.entries.items():
            self.obj.properties[prop] = var.get()
        try:
            self.obj.width = float(self.width_var.get())
            self.obj.height = float(self.height_var.get())
        except ValueError:
            pass

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


class BlockDiagramWindow(SysMLDiagramWindow):
    def __init__(self, master):
        tools = [
            "Block",
            "Association",
        ]
        super().__init__(master, "Block Diagram", tools)


class InternalBlockDiagramWindow(SysMLDiagramWindow):
    def __init__(self, master):
        tools = [
            "Block",
            "Part",
            "Port",
            "Connector",
        ]
        super().__init__(master, "Internal Block Diagram", tools)
