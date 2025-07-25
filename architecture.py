import tkinter as tk
from tkinter import ttk, simpledialog
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from sysml_repository import SysMLRepository

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
    element_id: str | None = None
    width: float = 80.0
    height: float = 40.0
    properties: Dict[str, str] = field(default_factory=dict)


class SysMLDiagramWindow(tk.Toplevel):
    """Base window for simple SysML diagrams with zoom and pan support."""

    def __init__(self, master, title, tools, diagram_id: str | None = None):
        super().__init__(master)
        self.title(title)
        self.geometry("800x600")

        self.repo = SysMLRepository.get_instance()
        if diagram_id and diagram_id in self.repo.diagrams:
            diagram = self.repo.diagrams[diagram_id]
        else:
            diagram = self.repo.create_diagram(title, diag_id=diagram_id)
        self.diagram_id = diagram.diag_id
        self.protocol("WM_DELETE_WINDOW", self.on_close)

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
                    src_id = self.start.element_id
                    dst_id = obj.element_id
                    if src_id and dst_id:
                        rel = self.repo.create_relationship(t, src_id, dst_id)
                        self.repo.add_relationship_to_diagram(self.diagram_id, rel.rel_id)
                self.start = None
                self.redraw()
        elif t and t != "Select":
            element = self.repo.create_element(t)
            self.repo.add_element_to_diagram(self.diagram_id, element.elem_id)
            new_obj = SysMLObject(_get_next_id(), t, x / self.zoom, y / self.zoom,
                                  element_id=element.elem_id)
            if t == "Block":
                new_obj.height = 140.0
                new_obj.width = 160.0
            key = f"{t.replace(' ', '')}Usage"
            for prop in SYSML_PROPERTIES.get(key, []):
                new_obj.properties.setdefault(prop, "")
            element.properties.update(new_obj.properties)
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
            diag_id = self.repo.get_linked_diagram(obj.element_id)
            if diag_id and diag_id in self.repo.diagrams:
                diag = self.repo.diagrams[diag_id]
                if diag.diag_type == "Activity Diagram":
                    ActivityDiagramWindow(self.master, diagram_id=diag_id)
                    return
                if diag.diag_type == "Internal Block Diagram":
                    InternalBlockDiagramWindow(self.master, diagram_id=diag_id)
                    return
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
        elif obj.obj_type in ("Action", "Part", "Port"):
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
        elif obj.obj_type == "Block":
            left, top = x - w, y - h
            right, bottom = x + w, y + h
            self.canvas.create_rectangle(left, top, right, bottom)
            header = f"<<block>> {obj.properties.get('name', '')}".strip()
            self.canvas.create_line(left, top + 20 * self.zoom, right, top + 20 * self.zoom)
            self.canvas.create_text(x, top + 10 * self.zoom, text=header, anchor="center")
            compartments = [
                ("Attributes", obj.properties.get("valueProperties", "")),
                ("Parts", obj.properties.get("partProperties", "")),
                ("References", obj.properties.get("referenceProperties", "")),
                ("Operations", obj.properties.get("operations", "")),
                ("Constraints", obj.properties.get("constraintProperties", "")),
                ("Ports", obj.properties.get("ports", "")),
            ]
            cy = top + 20 * self.zoom
            for label, text in compartments:
                self.canvas.create_line(left, cy, right, cy)
                if text:
                    self.canvas.create_text(x, cy + 10 * self.zoom, text=f"{label}: {text}", anchor="n")
                cy += 20 * self.zoom
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

    def on_close(self):
        self.repo.delete_diagram(self.diagram_id)
        self.destroy()

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

        repo = SysMLRepository.get_instance()
        if self.obj.obj_type == "Use Case":
            diags = [d for d in repo.diagrams.values() if d.diag_type == "Activity Diagram"]
            names = [d.name or d.diag_id for d in diags]
            ids = {d.name or d.diag_id: d.diag_id for d in diags}
            ttk.Label(master, text="Activity Diagram:").grid(row=row, column=0, sticky="e", padx=4, pady=2)
            self.diag_map = ids
            cur_id = repo.get_linked_diagram(self.obj.element_id)
            cur_name = next((n for n, i in ids.items() if i == cur_id), "")
            self.diagram_var = tk.StringVar(value=cur_name)
            ttk.Combobox(master, textvariable=self.diagram_var, values=list(ids.keys())).grid(row=row, column=1, padx=4, pady=2)
            row += 1
        elif self.obj.obj_type == "Block":
            diags = [d for d in repo.diagrams.values() if d.diag_type == "Internal Block Diagram"]
            names = [d.name or d.diag_id for d in diags]
            ids = {d.name or d.diag_id: d.diag_id for d in diags}
            ttk.Label(master, text="Internal Block Diagram:").grid(row=row, column=0, sticky="e", padx=4, pady=2)
            self.diag_map = ids
            cur_id = repo.get_linked_diagram(self.obj.element_id)
            cur_name = next((n for n, i in ids.items() if i == cur_id), "")
            self.diagram_var = tk.StringVar(value=cur_name)
            ttk.Combobox(master, textvariable=self.diagram_var, values=list(ids.keys())).grid(row=row, column=1, padx=4, pady=2)
            row += 1
        
    def apply(self):
        self.obj.properties["name"] = self.name_var.get()
        repo = SysMLRepository.get_instance()
        if self.obj.element_id and self.obj.element_id in repo.elements:
            repo.elements[self.obj.element_id].name = self.name_var.get()
        for prop, var in self.entries.items():
            self.obj.properties[prop] = var.get()
            if self.obj.element_id and self.obj.element_id in repo.elements:
                repo.elements[self.obj.element_id].properties[prop] = var.get()
        try:
            self.obj.width = float(self.width_var.get())
            self.obj.height = float(self.height_var.get())
        except ValueError:
            pass
        # Update linked diagram if applicable
        if hasattr(self, "diagram_var"):
            name = self.diagram_var.get()
            diag_id = self.diag_map.get(name)
            repo.link_diagram(self.obj.element_id, diag_id)

class UseCaseDiagramWindow(SysMLDiagramWindow):
    def __init__(self, master, diagram_id: str | None = None):
        tools = [
            "Actor",
            "Use Case",
            "System Boundary",
            "Association",
            "Include",
            "Extend",
        ]
        super().__init__(master, "Use Case Diagram", tools, diagram_id)


class ActivityDiagramWindow(SysMLDiagramWindow):
    def __init__(self, master, diagram_id: str | None = None):
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
        super().__init__(master, "Activity Diagram", tools, diagram_id)


class BlockDiagramWindow(SysMLDiagramWindow):
    def __init__(self, master, diagram_id: str | None = None):
        tools = [
            "Block",
            "Association",
        ]
        super().__init__(master, "Block Diagram", tools, diagram_id)


class InternalBlockDiagramWindow(SysMLDiagramWindow):
    def __init__(self, master, diagram_id: str | None = None):
        tools = [
            "Block",
            "Part",
            "Port",
            "Connector",
        ]
        super().__init__(master, "Internal Block Diagram", tools, diagram_id)


class NewDiagramDialog(simpledialog.Dialog):
    """Dialog to create a new diagram and assign a name and type."""

    def __init__(self, master):
        self.name = ""
        self.diag_type = "Use Case Diagram"
        super().__init__(master, title="New Diagram")

    def body(self, master):
        ttk.Label(master, text="Name:").grid(row=0, column=0, padx=4, pady=4, sticky="e")
        self.name_var = tk.StringVar()
        ttk.Entry(master, textvariable=self.name_var).grid(row=0, column=1, padx=4, pady=4)
        ttk.Label(master, text="Type:").grid(row=1, column=0, padx=4, pady=4, sticky="e")
        self.type_var = tk.StringVar(value=self.diag_type)
        ttk.Combobox(master, textvariable=self.type_var,
                     values=["Use Case Diagram", "Activity Diagram", "Block Diagram", "Internal Block Diagram"]).grid(row=1, column=1, padx=4, pady=4)

    def apply(self):
        self.name = self.name_var.get()
        self.diag_type = self.type_var.get()


class DiagramManagerDialog(tk.Toplevel):
    """Simple manager to browse and open architecture diagrams."""

    def __init__(self, master):
        super().__init__(master)
        self.title("Diagrams")
        self.repo = SysMLRepository.get_instance()
        self.geometry("300x300")
        self.listbox = tk.Listbox(self)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        btns = ttk.Frame(self)
        btns.pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(btns, text="Open", command=self.open).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="New", command=self.new).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Delete", command=self.delete).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Close", command=self.destroy).pack(side=tk.RIGHT, padx=2)
        self.refresh()

    def refresh(self):
        self.listbox.delete(0, tk.END)
        for d in self.repo.diagrams.values():
            name = d.name or d.diag_id
            self.listbox.insert(tk.END, f"{d.diag_id} | {name} ({d.diag_type})")

    def selected_id(self) -> str | None:
        if not self.listbox.curselection():
            return None
        value = self.listbox.get(self.listbox.curselection()[0])
        return value.split(" | ")[0]

    def open(self):
        diag_id = self.selected_id()
        if not diag_id:
            return
        self.open_diagram(diag_id)

    def open_diagram(self, diag_id: str):
        diag = self.repo.diagrams.get(diag_id)
        if not diag:
            return
        if diag.diag_type == "Use Case Diagram":
            UseCaseDiagramWindow(self, diagram_id=diag_id)
        elif diag.diag_type == "Activity Diagram":
            ActivityDiagramWindow(self, diagram_id=diag_id)
        elif diag.diag_type == "Block Diagram":
            BlockDiagramWindow(self, diagram_id=diag_id)
        elif diag.diag_type == "Internal Block Diagram":
            InternalBlockDiagramWindow(self, diagram_id=diag_id)

    def new(self):
        dlg = NewDiagramDialog(self)
        if dlg.name:
            self.repo.create_diagram(dlg.diag_type, name=dlg.name)
            self.refresh()

    def delete(self):
        diag_id = self.selected_id()
        if diag_id:
            self.repo.delete_diagram(diag_id)
            self.refresh()
