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


@dataclass
class DiagramConnection:
    src: int
    dst: int
    conn_type: str
    style: str = "Straight"  # Straight, Squared, Custom
    points: List[Tuple[float, float]] = field(default_factory=list)


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
            diagram = self.repo.create_diagram(title, name=title, diag_id=diagram_id)
        self.diagram_id = diagram.diag_id
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Load any saved objects and connections for this diagram
        self.objects: List[SysMLObject] = [
            SysMLObject(**data) for data in getattr(diagram, "objects", [])
        ]
        self.connections: List[DiagramConnection] = [
            DiagramConnection(**data) for data in getattr(diagram, "connections", [])
        ]
        if self.objects:
            global _next_obj_id
            _next_obj_id = max(o.obj_id for o in self.objects) + 1

        self.zoom = 1.0
        self.current_tool = None
        self.start = None
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
                    conn = DiagramConnection(self.start.obj_id, obj.obj_id, t)
                    self.connections.append(conn)
                    src_id = self.start.element_id
                    dst_id = obj.element_id
                    if src_id and dst_id:
                        rel = self.repo.create_relationship(t, src_id, dst_id)
                        self.repo.add_relationship_to_diagram(self.diagram_id, rel.rel_id)
                    ConnectionDialog(self, conn)
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
        if self.selected_obj.obj_type == "Port" and "parent" in self.selected_obj.properties:
            parent = self.get_object(int(self.selected_obj.properties["parent"]))
            if parent:
                self.selected_obj.x = x / self.zoom
                self.selected_obj.y = y / self.zoom
                self.snap_port_to_parent(self.selected_obj, parent)
        else:
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
        else:
            conn = self.find_connection(x, y)
            if conn:
                ConnectionDialog(self, conn)
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

    def _dist_to_segment(self, p, a, b) -> float:
        px, py = p
        ax, ay = a
        bx, by = b
        if ax == bx and ay == by:
            return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
        t = ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2)
        t = max(0, min(1, t))
        lx = ax + t * (bx - ax)
        ly = ay + t * (by - ay)
        return ((px - lx) ** 2 + (py - ly) ** 2) ** 0.5

    def find_connection(self, x: float, y: float) -> DiagramConnection | None:
        for conn in self.connections:
            src = self.get_object(conn.src)
            dst = self.get_object(conn.dst)
            if not src or not dst:
                continue
            points = [(src.x * self.zoom, src.y * self.zoom)]
            if conn.style == "Squared":
                midx = (src.x + dst.x) / 2 * self.zoom
                points.extend([(midx, points[-1][1]), (midx, dst.y * self.zoom)])
            elif conn.style == "Custom":
                for px, py in conn.points:
                    xpt = px * self.zoom
                    ypt = py * self.zoom
                    last = points[-1]
                    points.extend([(xpt, last[1]), (xpt, ypt)])
            points.append((dst.x * self.zoom, dst.y * self.zoom))
            for a, b in zip(points[:-1], points[1:]):
                if self._dist_to_segment((x, y), a, b) <= 5:
                    return conn
        return None

    def snap_port_to_parent(self, port: SysMLObject, parent: SysMLObject) -> None:
        px = port.x
        py = port.y
        left = parent.x - parent.width / 2
        right = parent.x + parent.width / 2
        top = parent.y - parent.height / 2
        bottom = parent.y + parent.height / 2
        d_left = abs(px - left)
        d_right = abs(px - right)
        d_top = abs(py - top)
        d_bottom = abs(py - bottom)
        min_d = min(d_left, d_right, d_top, d_bottom)
        if min_d == d_left:
            port.x = left
            port.y = min(max(py, top), bottom)
            port.properties["side"] = "W"
        elif min_d == d_right:
            port.x = right
            port.y = min(max(py, top), bottom)
            port.properties["side"] = "E"
        elif min_d == d_top:
            port.y = top
            port.x = min(max(px, left), right)
            port.properties["side"] = "N"
        else:
            port.y = bottom
            port.x = min(max(px, left), right)
            port.properties["side"] = "S"

    def edge_point(self, obj: SysMLObject, tx: float, ty: float) -> Tuple[float, float]:
        x = obj.x * self.zoom
        y = obj.y * self.zoom
        if obj.obj_type == "Port":
            return x, y
        w = obj.width * self.zoom / 2
        h = obj.height * self.zoom / 2
        dx = tx - x
        dy = ty - y
        if abs(dx) > abs(dy):
            if dx > 0:
                x += w
                y += dy * (w / abs(dx)) if dx != 0 else 0
            else:
                x -= w
                y += dy * (w / abs(dx)) if dx != 0 else 0
        else:
            if dy > 0:
                y += h
                x += dx * (h / abs(dy)) if dy != 0 else 0
            else:
                y -= h
                x += dx * (h / abs(dy)) if dy != 0 else 0
        return x, y

    def sync_ports(self, part: SysMLObject) -> None:
        names: List[str] = []
        block_id = part.properties.get("definition")
        if block_id and block_id in self.repo.elements:
            block_elem = self.repo.elements[block_id]
            names.extend([p.strip() for p in block_elem.properties.get("ports", "").split(",") if p.strip()])
        names.extend([p.strip() for p in part.properties.get("ports", "").split(",") if p.strip()])
        existing = {o.properties.get("name"): o for o in self.objects if o.obj_type == "Port" and o.properties.get("parent") == str(part.obj_id)}
        for n in names:
            if n not in existing:
                port = SysMLObject(_get_next_id(), "Port", part.x + part.width/2 + 20, part.y,
                                   properties={"name": n, "parent": str(part.obj_id), "side": "E"})
                self.snap_port_to_parent(port, part)
                self.objects.append(port)
                existing[n] = port
        for n, obj in list(existing.items()):
            if n not in names:
                self.objects.remove(obj)

    def zoom_in(self):
        self.zoom *= 1.2
        self.redraw()

    def zoom_out(self):
        self.zoom /= 1.2
        self.redraw()

    def redraw(self):
        self.canvas.delete("all")
        for obj in list(self.objects):
            if obj.obj_type == "Part":
                self.sync_ports(obj)
            self.draw_object(obj)
        for conn in self.connections:
            src = self.get_object(conn.src)
            dst = self.get_object(conn.dst)
            if src and dst:
                self.draw_connection(src, dst, conn)
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
                side = obj.properties.get("side", "E")
                sz = 10 * self.zoom
                if side == "E":
                    pts = [
                        (x - sz, y - sz),
                        (x - sz, y + sz),
                        (x + sz, y)
                    ]
                elif side == "W":
                    pts = [
                        (x + sz, y - sz),
                        (x + sz, y + sz),
                        (x - sz, y)
                    ]
                elif side == "N":
                    pts = [
                        (x - sz, y + sz),
                        (x + sz, y + sz),
                        (x, y - sz)
                    ]
                else:
                    pts = [
                        (x - sz, y - sz),
                        (x + sz, y - sz),
                        (x, y + sz)
                    ]
                self.canvas.create_polygon(*pts, fill="black")
            else:
                self.canvas.create_rectangle(x - w, y - h, x + w, y + h,
                                            dash=dash, fill=fill)
        elif obj.obj_type == "Block":
            left, top = x - w, y - h
            right, bottom = x + w, y + h
            self.canvas.create_rectangle(left, top, right, bottom)
            header = f"<<block>> {obj.properties.get('name', '')}".strip()
            self.canvas.create_line(left, top + 20 * self.zoom, right, top + 20 * self.zoom)
            self.canvas.create_text(left + 4 * self.zoom, top + 10 * self.zoom, text=header, anchor="w")
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
                display = f"{label}: {text}" if text else f"{label}:"
                self.canvas.create_text(left + 4 * self.zoom, cy + 10 * self.zoom, text=display, anchor="w")
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

        if obj.obj_type != "Block":
            label_lines = [obj.properties.get("name", obj.obj_type)]
            key = f"{obj.obj_type.replace(' ', '')}Usage"
            for prop in SYSML_PROPERTIES.get(key, []):
                val = obj.properties.get(prop)
                if val:
                    label_lines.append(f"{prop}: {val}")
            self.canvas.create_text(x, y, text="\n".join(label_lines), anchor="center")

    def draw_connection(self, a: SysMLObject, b: SysMLObject, conn: DiagramConnection):
        axc, ayc = a.x * self.zoom, a.y * self.zoom
        bxc, byc = b.x * self.zoom, b.y * self.zoom
        ax, ay = self.edge_point(a, bxc, byc)
        bx, by = self.edge_point(b, axc, ayc)
        dash = ()
        label = None
        if conn.conn_type in ("Include", "Extend"):
            dash = (4, 2)
            label = f"<<{conn.conn_type.lower()}>>"
        points = [(ax, ay)]
        if conn.style == "Squared":
            midx = (ax + bx) / 2
            points.extend([(midx, ay), (midx, by)])
        elif conn.style == "Custom":
            for px, py in conn.points:
                x = px * self.zoom
                y = py * self.zoom
                last = points[-1]
                points.extend([(x, last[1]), (x, y)])
        points.append((bx, by))
        flat = [coord for pt in points for coord in pt]
        self.canvas.create_line(*flat, arrow=tk.LAST, dash=dash)
        if label:
            mx, my = (ax + bx) / 2, (ay + by) / 2
            self.canvas.create_text(mx, my - 10 * self.zoom, text=label)

    def get_object(self, oid: int) -> SysMLObject | None:
        for o in self.objects:
            if o.obj_id == oid:
                return o
        return None

    def on_close(self):
        diag = self.repo.diagrams.get(self.diagram_id)
        if diag:
            diag.objects = [obj.__dict__ for obj in self.objects]
            diag.connections = [conn.__dict__ for conn in self.connections]
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
        self.listboxes = {}
        row = 3
        key = f"{self.obj.obj_type.replace(' ', '')}Usage"
        list_props = {
            "ports",
            "partProperties",
            "referenceProperties",
            "valueProperties",
            "constraintProperties",
            "operations",
        }
        for prop in SYSML_PROPERTIES.get(key, []):
            ttk.Label(master, text=f"{prop}:").grid(row=row, column=0, sticky="e", padx=4, pady=2)
            if prop in list_props:
                lb = tk.Listbox(master, height=4)
                items = [p.strip() for p in self.obj.properties.get(prop, "").split(",") if p.strip()]
                for it in items:
                    lb.insert(tk.END, it)
                lb.grid(row=row, column=1, padx=4, pady=2, sticky="we")
                btnf = ttk.Frame(master)
                btnf.grid(row=row, column=2, padx=2)
                ttk.Button(btnf, text="Add", command=lambda p=prop: self.add_list_item(p)).pack(side=tk.TOP)
                ttk.Button(btnf, text="Remove", command=lambda p=prop: self.remove_list_item(p)).pack(side=tk.TOP)
                self.listboxes[prop] = lb
            elif prop == "direction":
                var = tk.StringVar(value=self.obj.properties.get(prop, "in"))
                ttk.Combobox(master, textvariable=var, values=["in", "out", "inout"]).grid(row=row, column=1, padx=4, pady=2)
                self.entries[prop] = var
            else:
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
        elif self.obj.obj_type == "Part":
            blocks = [e for e in repo.elements.values() if e.elem_type == "Block"]
            idmap = {b.name or b.elem_id: b.elem_id for b in blocks}
            ttk.Label(master, text="Definition:").grid(row=row, column=0, sticky="e", padx=4, pady=2)
            self.def_map = idmap
            cur_id = self.obj.properties.get("definition", "")
            cur_name = next((n for n, i in idmap.items() if i == cur_id), "")
            self.def_var = tk.StringVar(value=cur_name)
            ttk.Combobox(master, textvariable=self.def_var, values=list(idmap.keys())).grid(row=row, column=1, padx=4, pady=2)
            row += 1

    def add_port(self):
        name = simpledialog.askstring("Port", "Name:", parent=self)
        if name:
            self.listboxes["ports"].insert(tk.END, name)

    def remove_port(self):
        sel = list(self.listboxes["ports"].curselection())
        for idx in reversed(sel):
            self.listboxes["ports"].delete(idx)

    def add_list_item(self, prop: str):
        val = simpledialog.askstring(prop, "Value:", parent=self)
        if val:
            self.listboxes[prop].insert(tk.END, val)

    def remove_list_item(self, prop: str):
        lb = self.listboxes[prop]
        sel = list(lb.curselection())
        for idx in reversed(sel):
            lb.delete(idx)
        
    def apply(self):
        self.obj.properties["name"] = self.name_var.get()
        repo = SysMLRepository.get_instance()
        if self.obj.element_id and self.obj.element_id in repo.elements:
            repo.elements[self.obj.element_id].name = self.name_var.get()
        for prop, var in self.entries.items():
            self.obj.properties[prop] = var.get()
            if self.obj.element_id and self.obj.element_id in repo.elements:
                repo.elements[self.obj.element_id].properties[prop] = var.get()
        for prop, lb in self.listboxes.items():
            items = [lb.get(i) for i in range(lb.size())]
            joined = ", ".join(items)
            self.obj.properties[prop] = joined
            if self.obj.element_id and self.obj.element_id in repo.elements:
                repo.elements[self.obj.element_id].properties[prop] = joined
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
        if hasattr(self, "def_var"):
            name = self.def_var.get()
            def_id = self.def_map.get(name)
            if def_id:
                self.obj.properties["definition"] = def_id
                if self.obj.element_id and self.obj.element_id in repo.elements:
                    repo.elements[self.obj.element_id].properties["definition"] = def_id


class ConnectionDialog(simpledialog.Dialog):
    """Edit connection style and custom routing points."""

    def __init__(self, master, connection: DiagramConnection):
        self.connection = connection
        super().__init__(master, title="Connection Properties")

    def body(self, master):
        ttk.Label(master, text="Style:").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        self.style_var = tk.StringVar(value=self.connection.style)
        ttk.Combobox(master, textvariable=self.style_var,
                     values=["Straight", "Squared", "Custom"]).grid(row=0, column=1, padx=4, pady=4)
        ttk.Label(master, text="Points:").grid(row=1, column=0, sticky="ne", padx=4, pady=4)
        self.point_list = tk.Listbox(master, height=4)
        for px, py in self.connection.points:
            self.point_list.insert(tk.END, f"{px:.1f},{py:.1f}")
        self.point_list.grid(row=1, column=1, padx=4, pady=4, sticky="we")
        btnf = ttk.Frame(master)
        btnf.grid(row=1, column=2, padx=2)
        ttk.Button(btnf, text="Add", command=self.add_point).pack(side=tk.TOP)
        ttk.Button(btnf, text="Remove", command=self.remove_point).pack(side=tk.TOP)

    def add_point(self):
        x = simpledialog.askfloat("Point", "X:", parent=self)
        y = simpledialog.askfloat("Point", "Y:", parent=self)
        if x is not None and y is not None:
            self.point_list.insert(tk.END, f"{x},{y}")

    def remove_point(self):
        sel = list(self.point_list.curselection())
        for idx in reversed(sel):
            self.point_list.delete(idx)

    def apply(self):
        self.connection.style = self.style_var.get()
        pts = []
        for i in range(self.point_list.size()):
            txt = self.point_list.get(i)
            try:
                x_str, y_str = txt.split(",")
                pts.append((float(x_str), float(y_str)))
            except ValueError:
                continue
        self.connection.points = pts

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


class DiagramPropertiesDialog(simpledialog.Dialog):
    """Dialog to edit a diagram's metadata."""

    def __init__(self, master, diagram: SysMLDiagram):
        self.diagram = diagram
        super().__init__(master, title="Diagram Properties")

    def body(self, master):
        ttk.Label(master, text="Name:").grid(row=0, column=0, sticky="e", padx=4, pady=2)
        self.name_var = tk.StringVar(value=self.diagram.name)
        ttk.Entry(master, textvariable=self.name_var).grid(row=0, column=1, padx=4, pady=2)
        ttk.Label(master, text="Description:").grid(row=1, column=0, sticky="e", padx=4, pady=2)
        self.desc_var = tk.StringVar(value=getattr(self.diagram, "description", ""))
        ttk.Entry(master, textvariable=self.desc_var).grid(row=1, column=1, padx=4, pady=2)
        ttk.Label(master, text="Color:").grid(row=2, column=0, sticky="e", padx=4, pady=2)
        self.color_var = tk.StringVar(value=getattr(self.diagram, "color", "#FFFFFF"))
        ttk.Entry(master, textvariable=self.color_var).grid(row=2, column=1, padx=4, pady=2)

    def apply(self):
        self.diagram.name = self.name_var.get()
        self.diagram.description = self.desc_var.get()
        self.diagram.color = self.color_var.get()


class ArchitectureManagerDialog(tk.Toplevel):
    """Manage packages and diagrams in a hierarchical tree."""

    def __init__(self, master):
        super().__init__(master)
        self.title("Architecture")
        self.repo = SysMLRepository.get_instance()
        self.geometry("350x400")
        self.tree = ttk.Treeview(self)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        btns = ttk.Frame(self)
        btns.pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(btns, text="Open", command=self.open).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Properties", command=self.properties).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="New Package", command=self.new_package).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="New Diagram", command=self.new_diagram).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Delete", command=self.delete).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Close", command=self.destroy).pack(side=tk.RIGHT, padx=2)
        self.populate()
        self.tree.bind("<Double-1>", self.on_double)

    def populate(self):
        self.tree.delete(*self.tree.get_children())

        def add_pkg(pkg_id, parent=""):
            pkg = self.repo.elements[pkg_id]
            node = self.tree.insert(parent, "end", iid=pkg_id, text=pkg.name or pkg_id, open=True)
            for p in self.repo.elements.values():
                if p.elem_type == "Package" and p.owner == pkg_id:
                    add_pkg(p.elem_id, node)
            for d in self.repo.diagrams.values():
                if d.package == pkg_id:
                    label = d.name or d.diag_id
                    self.tree.insert(node, "end", iid=f"diag_{d.diag_id}", text=label, values=(d.diag_type,))

        add_pkg(self.repo.root_package.elem_id)

    def selected(self):
        sel = self.tree.selection()
        if sel:
            return sel[0]
        item = self.tree.focus()
        return item if item else None

    def open(self):
        item = self.selected()
        if item and item.startswith("diag_"):
            self.open_diagram(item[5:])

    def on_double(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            if item.startswith("diag_"):
                self.open_diagram(item[5:])

    def open_diagram(self, diag_id: str):
        diag = self.repo.diagrams.get(diag_id)
        if not diag:
            return
        master = self.master if self.master else self
        if diag.diag_type == "Use Case Diagram":
            UseCaseDiagramWindow(master, diagram_id=diag_id)
        elif diag.diag_type == "Activity Diagram":
            ActivityDiagramWindow(master, diagram_id=diag_id)
        elif diag.diag_type == "Block Diagram":
            BlockDiagramWindow(master, diagram_id=diag_id)
        elif diag.diag_type == "Internal Block Diagram":
            InternalBlockDiagramWindow(master, diagram_id=diag_id)

    def new_package(self):
        item = self.selected() or self.repo.root_package.elem_id
        if item.startswith("diag_"):
            item = self.repo.diagrams[item[5:]].package
        name = simpledialog.askstring("New Package", "Name:")
        if name:
            self.repo.create_package(name, parent=item)
            self.populate()

    def new_diagram(self):
        item = self.selected() or self.repo.root_package.elem_id
        if item.startswith("diag_"):
            item = self.repo.diagrams[item[5:]].package
        dlg = NewDiagramDialog(self)
        if dlg.name:
            self.repo.create_diagram(dlg.diag_type, name=dlg.name, package=item)
            self.populate()

    def delete(self):
        item = self.selected()
        if not item:
            return
        if item.startswith("diag_"):
            self.repo.delete_diagram(item[5:])
        else:
            self.repo.delete_package(item)
        self.populate()

    def properties(self):
        item = self.selected()
        if item and item.startswith("diag_"):
            diag = self.repo.diagrams.get(item[5:])
            if diag:
                DiagramPropertiesDialog(self, diag)
                self.populate()
