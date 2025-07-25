import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from sysml_repository import SysMLRepository, SysMLDiagram

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

    def __init__(self, master, title, tools, diagram_id: str | None = None, app=None):
        super().__init__(master)
        self.app = app
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
        self.clipboard: SysMLObject | None = None
        self.resizing_obj: SysMLObject | None = None
        self.resize_edge: str | None = None

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
        self.bind("<Control-c>", self.copy_selected)
        self.bind("<Control-x>", self.cut_selected)
        self.bind("<Control-v>", self.paste_selected)
        self.bind("<Delete>", self.delete_selected)

        self.redraw()

    def select_tool(self, tool):
        self.current_tool = tool
        self.start = None
        cursor = "arrow"
        if tool != "Select":
            cursor = "crosshair" if tool in (
                "Association",
                "Include",
                "Extend",
                "Flow",
                "Connector",
            ) else "tcross"
        self.canvas.configure(cursor=cursor)

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
            pkg = self.repo.diagrams[self.diagram_id].package
            element = self.repo.create_element(t, owner=pkg)
            self.repo.add_element_to_diagram(self.diagram_id, element.elem_id)
            new_obj = SysMLObject(_get_next_id(), t, x / self.zoom, y / self.zoom,
                                  element_id=element.elem_id)
            if t == "Block":
                new_obj.height = 140.0
                new_obj.width = 160.0
            elif t == "System Boundary":
                new_obj.width = 200.0
                new_obj.height = 120.0
            elif t in ("Decision", "Merge"):
                new_obj.width = 40.0
                new_obj.height = 40.0
            elif t == "Initial":
                new_obj.width = 20.0
                new_obj.height = 20.0
            elif t == "Final":
                new_obj.width = 30.0
                new_obj.height = 30.0
            elif t in ("Fork", "Join"):
                new_obj.width = 60.0
                new_obj.height = 10.0
            key = f"{t.replace(' ', '')}Usage"

            for prop in SYSML_PROPERTIES.get(key, []):
                new_obj.properties.setdefault(prop, "")
            if t == "Port":
                new_obj.properties.setdefault("labelX", "8")
                new_obj.properties.setdefault("labelY", "-8")
            element.properties.update(new_obj.properties)
            self.objects.append(new_obj)
            self.redraw()
        else:
            if obj:
                self.selected_obj = obj
                self.drag_offset = (x / self.zoom - obj.x, y / self.zoom - obj.y)
                self.resizing_obj = None
                self.resize_edge = self.hit_resize_handle(obj, x, y)
                if self.resize_edge:
                    self.resizing_obj = obj
                self.redraw()
            else:
                # allow clicking on the resize handle even if outside the object
                if self.selected_obj:
                    self.resize_edge = self.hit_resize_handle(self.selected_obj, x, y)
                    if self.resize_edge:
                        self.resizing_obj = self.selected_obj
                        return
                self.selected_obj = None
                self.resizing_obj = None
                self.resize_edge = None
                self.redraw()

    def on_left_drag(self, event):
        if not self.selected_obj:
            return
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        if self.resizing_obj:
            obj = self.resizing_obj
            cx = obj.x * self.zoom
            cy = obj.y * self.zoom
            if "e" in self.resize_edge or "w" in self.resize_edge:
                obj.width = max(10.0, 2 * abs(x - cx) / self.zoom)
            if "n" in self.resize_edge or "s" in self.resize_edge:
                if obj.obj_type not in ("Fork", "Join"):
                    obj.height = max(10.0, 2 * abs(y - cy) / self.zoom)
            self.redraw()
            return
        if self.selected_obj.obj_type == "Port" and "parent" in self.selected_obj.properties:
            parent = self.get_object(int(self.selected_obj.properties["parent"]))
            if parent:
                self.selected_obj.x = x / self.zoom
                self.selected_obj.y = y / self.zoom
                self.snap_port_to_parent(self.selected_obj, parent)
        else:
            old_x = self.selected_obj.x
            old_y = self.selected_obj.y
            self.selected_obj.x = x / self.zoom - self.drag_offset[0]
            self.selected_obj.y = y / self.zoom - self.drag_offset[1]
            dx = self.selected_obj.x - old_x
            dy = self.selected_obj.y - old_y
            if self.selected_obj.obj_type == "Part":
                for p in self.objects:
                    if p.obj_type == "Port" and p.properties.get("parent") == str(self.selected_obj.obj_id):
                        p.x += dx
                        p.y += dy
                        self.snap_port_to_parent(p, self.selected_obj)
        self.redraw()

    def on_left_release(self, _event):
        self.start = None
        self.resizing_obj = None
        self.resize_edge = None

    def on_double_click(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        obj = self.find_object(x, y)
        if obj:
            diag_id = self.repo.get_linked_diagram(obj.element_id)
            if diag_id and diag_id in self.repo.diagrams:
                diag = self.repo.diagrams[diag_id]
                if diag.diag_type == "Activity Diagram":
                    ActivityDiagramWindow(self.master, self.app, diagram_id=diag_id)
                    return
                if diag.diag_type == "Internal Block Diagram":
                    InternalBlockDiagramWindow(self.master, self.app, diagram_id=diag_id)
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

    def hit_resize_handle(self, obj: SysMLObject, x: float, y: float) -> str | None:
        margin = 5
        ox = obj.x * self.zoom
        oy = obj.y * self.zoom
        w = obj.width * self.zoom / 2
        h = obj.height * self.zoom / 2
        left = ox - w
        right = ox + w
        top = oy - h
        bottom = oy + h
        near_left = abs(x - left) <= margin
        near_right = abs(x - right) <= margin
        near_top = abs(y - top) <= margin
        near_bottom = abs(y - bottom) <= margin
        if near_left and near_top:
            return "nw"
        if near_right and near_top:
            return "ne"
        if near_left and near_bottom:
            return "sw"
        if near_right and near_bottom:
            return "se"
        if near_left:
            return "w"
        if near_right:
            return "e"
        if near_top:
            return "n"
        if near_bottom:
            return "s"
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
                port = SysMLObject(
                    _get_next_id(),
                    "Port",
                    part.x + part.width / 2 + 20,
                    part.y,
                    properties={
                        "name": n,
                        "parent": str(part.obj_id),
                        "side": "E",
                        "labelX": "8",
                        "labelY": "-8",
                    },
                )
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
            sx = obj.width / 80.0 * self.zoom
            sy = obj.height / 40.0 * self.zoom
            self.canvas.create_oval(x - 10 * sx, y - 30 * sy,
                                    x + 10 * sx, y - 10 * sy)
            self.canvas.create_line(x, y - 10 * sy, x, y + 20 * sy)
            self.canvas.create_line(x - 15 * sx, y, x + 15 * sx, y)
            self.canvas.create_line(x, y + 20 * sy,
                                    x - 10 * sx, y + 40 * sy)
            self.canvas.create_line(x, y + 20 * sy,
                                    x + 10 * sx, y + 40 * sy)
        elif obj.obj_type == "Use Case":
            self.canvas.create_oval(x - w, y - h, x + w, y + h)
        elif obj.obj_type == "System Boundary":
            self.canvas.create_rectangle(x - w, y - h, x + w, y + h,
                                        dash=(4, 2))
            label = obj.properties.get("name", "")
            if label:
                lx = x - w + 4 * self.zoom
                ly = y - h - 4 * self.zoom
                self.canvas.create_text(lx, ly, text=label, anchor="sw")
        elif obj.obj_type in ("Action Usage", "Action", "Part", "Port"):
            dash = ()
            fill = ""
            if obj.obj_type == "Part":
                dash = (4, 2)
            if obj.obj_type == "Port":
                side = obj.properties.get("side", "E")
                sz = 6 * self.zoom
                self.canvas.create_rectangle(x - sz, y - sz, x + sz, y + sz, fill="white")
                arrow_len = sz * 1.2
                direction = obj.properties.get("direction", "out")
                if direction == "in":
                    self.canvas.create_line(x + arrow_len/2, y, x - arrow_len/2, y, arrow=tk.LAST)
                elif direction == "out":
                    self.canvas.create_line(x - arrow_len/2, y, x + arrow_len/2, y, arrow=tk.LAST)
                else:
                    self.canvas.create_line(x - arrow_len/2, y, x + arrow_len/2, y, arrow=tk.BOTH)
                lx = x + float(obj.properties.get("labelX", "8")) * self.zoom
                ly = y + float(obj.properties.get("labelY", "-8")) * self.zoom
                self.canvas.create_text(lx, ly, text=obj.properties.get("name", ""), anchor="center")
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
                (
                    "Reliability",
                    " ".join(
                        f"{label}={obj.properties.get(key,'')}"
                        for label, key in (
                            ("FIT", "fit"),
                            ("Qual", "qualification"),
                            ("FM", "failureModes"),
                        )
                        if obj.properties.get(key, "")
                    ),
                ),
            ]
            cy = top + 20 * self.zoom
            for label, text in compartments:
                self.canvas.create_line(left, cy, right, cy)
                display = f"{label}: {text}" if text else f"{label}:"
                self.canvas.create_text(left + 4 * self.zoom, cy + 10 * self.zoom, text=display, anchor="w")
                cy += 20 * self.zoom
        elif obj.obj_type in ("Initial", "Final"):
            if obj.obj_type == "Initial":
                r = min(obj.width, obj.height) / 2 * self.zoom
                self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="black")
            else:
                r = min(obj.width, obj.height) / 2 * self.zoom
                inner = max(r - 5 * self.zoom, 0)
                self.canvas.create_oval(x - r, y - r, x + r, y + r)
                self.canvas.create_oval(x - inner, y - inner, x + inner, y + inner,
                                        fill="black")
        elif obj.obj_type in ("Decision", "Merge"):
            self.canvas.create_polygon(x, y - h,
                                      x + w, y,
                                      x, y + h,
                                      x - w, y,
                                      fill="white", outline="black")
        elif obj.obj_type in ("Fork", "Join"):
            half = obj.width / 2 * self.zoom
            self.canvas.create_rectangle(x - half, y - 5 * self.zoom,
                                        x + half, y + 5 * self.zoom,
                                        fill="black")
        else:
            self.canvas.create_rectangle(x - w, y - h, x + w, y + h)

        if obj.obj_type not in ("Block", "System Boundary", "Port"):
            name = obj.properties.get("name", obj.obj_type)
            if obj.obj_type == "Part":
                def_id = obj.properties.get("definition")
                if def_id and def_id in self.repo.elements:
                    def_name = self.repo.elements[def_id].name or def_id
                    name = f"{name} : {def_name}"
            label_lines = [name]
            key = obj.obj_type.replace(' ', '')
            if not key.endswith('Usage'):
                key += 'Usage'
            for prop in SYSML_PROPERTIES.get(key, []):
                val = obj.properties.get(prop)
                if val:
                    label_lines.append(f"{prop}: {val}")
            if obj.obj_type == "Part":
                rel_items = []
                for lbl, key in (
                    ("FIT", "fit"),
                    ("Qual", "qualification"),
                    ("FM", "failureModes"),
                ):
                    val = obj.properties.get(key)
                    if val:
                        rel_items.append(f"{lbl}: {val}")
                if rel_items:
                    label_lines.extend(rel_items)
            self.canvas.create_text(x, y, text="\n".join(label_lines), anchor="center")

        if obj == self.selected_obj:
            bx = x - w
            by = y - h
            ex = x + w
            ey = y + h
            self.canvas.create_rectangle(bx, by, ex, ey, outline="red", dash=(2, 2))
            s = 4
            for hx, hy in [(bx, by), (bx, ey), (ex, by), (ex, ey)]:
                self.canvas.create_rectangle(hx - s, hy - s, hx + s, hy + s,
                                             outline="red", fill="white")

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

    # ------------------------------------------------------------
    # Clipboard operations
    # ------------------------------------------------------------
    def copy_selected(self, _event=None):
        if self.selected_obj:
            import copy
            self.clipboard = copy.deepcopy(self.selected_obj)

    def cut_selected(self, _event=None):
        if self.selected_obj:
            import copy
            self.clipboard = copy.deepcopy(self.selected_obj)
            self.remove_object(self.selected_obj)
            self.selected_obj = None
            self.redraw()

    def paste_selected(self, _event=None):
        if self.clipboard:
            import copy
            new_obj = copy.deepcopy(self.clipboard)
            new_obj.obj_id = _get_next_id()
            new_obj.x += 20
            new_obj.y += 20
            self.objects.append(new_obj)
            diag = self.repo.diagrams.get(self.diagram_id)
            if diag and new_obj.element_id and new_obj.element_id not in diag.elements:
                diag.elements.append(new_obj.element_id)
            self.selected_obj = new_obj
            self.redraw()

    def delete_selected(self, _event=None):
        if self.selected_obj:
            self.remove_object(self.selected_obj)
            self.selected_obj = None
            self.redraw()

    def remove_object(self, obj: SysMLObject) -> None:
        if obj in self.objects:
            self.objects.remove(obj)
        self.connections = [c for c in self.connections if c.src != obj.obj_id and c.dst != obj.obj_id]
        diag = self.repo.diagrams.get(self.diagram_id)
        if diag and obj.element_id in diag.elements:
            diag.elements.remove(obj.element_id)

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
        row = 2
        if self.obj.obj_type not in ("Fork", "Join"):
            ttk.Label(master, text="Height:").grid(row=2, column=0, sticky="e", padx=4, pady=2)
            self.height_var = tk.StringVar(value=str(self.obj.height))
            ttk.Entry(master, textvariable=self.height_var).grid(row=2, column=1, padx=4, pady=2)
            row = 3
        else:
            self.height_var = tk.StringVar(value=str(self.obj.height))
        self.entries = {}
        self.listboxes = {}
        key = f"{self.obj.obj_type.replace(' ', '')}Usage"
        list_props = {
            "ports",
            "partProperties",
            "referenceProperties",
            "valueProperties",
            "constraintProperties",
            "operations",
            "failureModes",
        }
        app = getattr(self.master, 'app', None)
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
            elif self.obj.obj_type == "Use Case" and prop == "useCaseDefinition":
                repo = SysMLRepository.get_instance()
                defs = [e for e in repo.elements.values() if e.elem_type == "Use Case"]
                idmap = {d.name or d.elem_id: d.elem_id for d in defs}
                self.ucdef_map = idmap
                cur_id = self.obj.properties.get(prop, "")
                cur_name = next((n for n, i in idmap.items() if i == cur_id), "")
                var = tk.StringVar(value=cur_name)
                ttk.Combobox(master, textvariable=var, values=list(idmap.keys())).grid(row=row, column=1, padx=4, pady=2)
                self.entries[prop] = var
            elif prop == "circuit" and app:
                circuits = [
                    c for ra in getattr(app, 'reliability_analyses', [])
                    for c in ra.components if c.comp_type == 'circuit'
                ]
                names = [c.name for c in circuits]
                var = tk.StringVar(value=self.obj.properties.get(prop, ""))
                cb = ttk.Combobox(master, textvariable=var, values=names, state="readonly")
                cb.grid(row=row, column=1, padx=4, pady=2)
                self.entries[prop] = var
                self._circuit_map = {c.name: c for c in circuits}

                def sync_circuit(_):
                    name = var.get()
                    comp = self._circuit_map.get(name)
                    if not comp:
                        return
                    if 'fit' in self.entries:
                        self.entries['fit'].set(f"{comp.fit:.2f}")
                    else:
                        self.obj.properties['fit'] = f"{comp.fit:.2f}"
                    if 'qualification' in self.entries:
                        self.entries['qualification'].set(comp.qualification)
                    else:
                        self.obj.properties['qualification'] = comp.qualification
                    modes = self._get_failure_modes(app, comp.name)
                    if 'failureModes' in self.entries:
                        self.entries['failureModes'].set(modes)
                    else:
                        self.obj.properties['failureModes'] = modes

                cb.bind("<<ComboboxSelected>>", sync_circuit)
            elif prop == "component" and app:
                comps = [
                    c for ra in getattr(app, 'reliability_analyses', [])
                    for c in ra.components if c.comp_type != 'circuit'
                ]
                names = [c.name for c in comps]
                var = tk.StringVar(value=self.obj.properties.get(prop, ""))
                cb = ttk.Combobox(master, textvariable=var, values=names, state="readonly")
                cb.grid(row=row, column=1, padx=4, pady=2)
                self.entries[prop] = var
                self._comp_map = {c.name: c for c in comps}

                def sync_component(_):
                    name = var.get()
                    comp = self._comp_map.get(name)
                    if not comp:
                        return
                    if 'fit' in self.entries:
                        self.entries['fit'].set(f"{comp.fit:.2f}")
                    else:
                        self.obj.properties['fit'] = f"{comp.fit:.2f}"
                    if 'qualification' in self.entries:
                        self.entries['qualification'].set(comp.qualification)
                    else:
                        self.obj.properties['qualification'] = comp.qualification
                    modes = self._get_failure_modes(app, comp.name)
                    if 'failureModes' in self.entries:
                        self.entries['failureModes'].set(modes)
                    else:
                        self.obj.properties['failureModes'] = modes

                cb.bind("<<ComboboxSelected>>", sync_component)
            else:
                var = tk.StringVar(value=self.obj.properties.get(prop, ""))
                state = "normal"
                if self.obj.obj_type == "Block" and prop in ("fit", "qualification"):
                    state = "readonly"
                ttk.Entry(master, textvariable=var, state=state).grid(row=row, column=1, padx=4, pady=2)
                self.entries[prop] = var
            row += 1

        repo = SysMLRepository.get_instance()
        if self.obj.obj_type == "Block":
            diags = [d for d in repo.diagrams.values() if d.diag_type == "Internal Block Diagram"]
            ids = {d.name or d.diag_id: d.diag_id for d in diags}
            ttk.Label(master, text="Internal Block Diagram:").grid(row=row, column=0, sticky="e", padx=4, pady=2)
            self.diag_map = ids
            cur_id = repo.get_linked_diagram(self.obj.element_id)
            cur_name = next((n for n, i in ids.items() if i == cur_id), "")
            self.diagram_var = tk.StringVar(value=cur_name)
            ttk.Combobox(master, textvariable=self.diagram_var, values=list(ids.keys())).grid(row=row, column=1, padx=4, pady=2)
            row += 1
        elif self.obj.obj_type in ("Action Usage", "Action"):
            diagrams = [
                d for d in repo.diagrams.values()
                if d.diag_type in ("Activity Diagram", "Internal Block Diagram")
            ]
            self.behavior_map = {d.name or d.diag_id: d.diag_id for d in diagrams}
            ttk.Label(master, text="Behavior Diagram:").grid(row=row, column=0, sticky="e", padx=4, pady=2)
            cur_id = repo.get_linked_diagram(self.obj.element_id)
            cur_name = next((n for n, i in self.behavior_map.items() if i == cur_id), "")
            self.behavior_var = tk.StringVar(value=cur_name)
            ttk.Combobox(master, textvariable=self.behavior_var, values=list(self.behavior_map.keys())).grid(row=row, column=1, padx=4, pady=2)
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

    def _get_failure_modes(self, app, comp_name: str) -> str:
        """Return comma separated failure modes for a component name."""
        modes = set()
        for e in getattr(app, 'fmea_entries', []):
            if getattr(e, 'fmea_component', '') == comp_name:
                label = getattr(e, 'description', '') or getattr(e, 'user_name', '')
                if label:
                    modes.add(label)
        for fmea in getattr(app, 'fmeas', []):
            for e in fmea.get('entries', []):
                if getattr(e, 'fmea_component', '') == comp_name:
                    label = getattr(e, 'description', '') or getattr(e, 'user_name', '')
                    if label:
                        modes.add(label)
        return ", ".join(sorted(modes))
        
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
        link_id = None
        if hasattr(self, "behavior_var") and self.behavior_var.get():
            link_id = self.behavior_map.get(self.behavior_var.get())
        elif hasattr(self, "diagram_var"):
            link_id = self.diag_map.get(self.diagram_var.get())
        if hasattr(self, "behavior_var") or hasattr(self, "diagram_var"):
            repo.link_diagram(self.obj.element_id, link_id)
        if hasattr(self, "def_var"):
            name = self.def_var.get()
            def_id = self.def_map.get(name)
            if def_id:
                self.obj.properties["definition"] = def_id
                if self.obj.element_id and self.obj.element_id in repo.elements:
                    repo.elements[self.obj.element_id].properties["definition"] = def_id
        if hasattr(self, "ucdef_var"):
            name = self.ucdef_var.get()
            def_id = self.ucdef_map.get(name)
            if def_id:
                self.obj.properties["useCaseDefinition"] = def_id
                if self.obj.element_id and self.obj.element_id in repo.elements:
                    repo.elements[self.obj.element_id].properties["useCaseDefinition"] = def_id
                    
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
    def __init__(self, master, app, diagram_id: str | None = None):
        tools = [
            "Actor",
            "Use Case",
            "System Boundary",
            "Association",
        ]
        super().__init__(master, "Use Case Diagram", tools, diagram_id, app=app)


class ActivityDiagramWindow(SysMLDiagramWindow):
    def __init__(self, master, app, diagram_id: str | None = None):
        tools = [
            "Action Usage",
            "Initial",
            "Final",
            "Decision",
            "Merge",
            "Fork",
            "Join",
            "Flow",
        ]
        super().__init__(master, "Activity Diagram", tools, diagram_id, app=app)


class BlockDiagramWindow(SysMLDiagramWindow):
    def __init__(self, master, app, diagram_id: str | None = None):
        tools = [
            "Block",
            "Association",
        ]
        super().__init__(master, "Block Diagram", tools, diagram_id, app=app)


class InternalBlockDiagramWindow(SysMLDiagramWindow):
    def __init__(self, master, app, diagram_id: str | None = None):
        tools = [
            "Part",
            "Port",
            "Connector",
        ]
        super().__init__(master, "Internal Block Diagram", tools, diagram_id, app=app)

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

    def __init__(self, master, app=None):
        super().__init__(master)
        self.app = app
        self.title("Architecture Explorer")
        self.repo = SysMLRepository.get_instance()
        self.geometry("350x400")
        self.tree = ttk.Treeview(self)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # simple colored square icons for packages, diagrams and elements
        self.pkg_icon = tk.PhotoImage(width=16, height=16)
        self.pkg_icon.put("#f4d742", to=(0, 0, 15, 15))
        self.diag_icon = tk.PhotoImage(width=16, height=16)
        self.diag_icon.put("#58a6ff", to=(0, 0, 15, 15))
        self.elem_icon = tk.PhotoImage(width=16, height=16)
        self.elem_icon.put("#7ec77e", to=(0, 0, 15, 15))
        btns = ttk.Frame(self)
        btns.pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(btns, text="Open", command=self.open).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Properties", command=self.properties).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="New Package", command=self.new_package).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="New Diagram", command=self.new_diagram).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Cut", command=self.cut).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Paste", command=self.paste).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Delete", command=self.delete).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Close", command=self.destroy).pack(side=tk.RIGHT, padx=2)
        self.populate()
        self.tree.bind("<Double-1>", self.on_double)
        self.tree.bind("<ButtonPress-1>", self.on_drag_start)
        self.tree.bind("<B1-Motion>", self.on_drag_motion)
        self.tree.bind("<ButtonRelease-1>", self.on_drag_release)
        self.bind("<FocusIn>", lambda _e: self.populate())
        self.drag_item = None
        self.cut_item = None

    def populate(self):
        self.tree.delete(*self.tree.get_children())

        root_pkg = getattr(self.repo, "root_package", None)
        if not root_pkg or root_pkg.elem_id not in self.repo.elements:
            # ensure a valid root package exists
            self.repo.root_package = self.repo.create_element("Package", name="Root")
            root_pkg = self.repo.root_package

        def add_pkg(pkg_id, parent=""):
            pkg = self.repo.elements[pkg_id]
            node = self.tree.insert(parent, "end", iid=pkg_id,
                                   text=pkg.name or pkg_id, open=True,
                                   image=self.pkg_icon)
            for p in self.repo.elements.values():
                if p.elem_type == "Package" and p.owner == pkg_id:
                    add_pkg(p.elem_id, node)
            for e in self.repo.elements.values():
                if e.owner == pkg_id and e.elem_type != "Package":
                    label = e.name or e.elem_id
                    self.tree.insert(node, "end", iid=e.elem_id, text=label,
                                     values=(e.elem_type,), image=self.elem_icon)
            for d in self.repo.diagrams.values():
                if d.package == pkg_id:
                    label = d.name or d.diag_id
                    self.tree.insert(node, "end", iid=f"diag_{d.diag_id}",
                                     text=label, values=(d.diag_type,), image=self.diag_icon)
                    for obj in d.objects:
                        name = obj.get("properties", {}).get("name", obj.get("obj_type"))
                        oid = obj.get("obj_id")
                        self.tree.insert(node, "end",
                                         iid=f"obj_{d.diag_id}_{oid}",
                                         text=name,
                                        values=(obj.get("obj_type"),),
                                         image=self.elem_icon)

        add_pkg(root_pkg.elem_id)

    def selected(self):
        sel = self.tree.selection()
        if sel:
            return sel[0]
        item = self.tree.focus()
        return item if item else None

    def open(self):
        item = self.selected()
        if not item:
            return
        if item.startswith("diag_"):
            self.open_diagram(item[5:])
        elif item.startswith("obj_"):
            diag_id, oid = item[4:].split("_", 1)
            win = self.open_diagram(diag_id)
            if win:
                for o in win.objects:
                    if o.obj_id == int(oid):
                        win.selected_obj = o
                        win.redraw()
                        break

    def on_double(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            if item.startswith("diag_"):
                self.open_diagram(item[5:])
            elif item.startswith("obj_"):
                self.open()

    def open_diagram(self, diag_id: str):
        diag = self.repo.diagrams.get(diag_id)
        if not diag:
            return None
        master = self.master if self.master else self
        win = None
        if diag.diag_type == "Use Case Diagram":
            UseCaseDiagramWindow(master, self.app, diagram_id=diag_id)
        elif diag.diag_type == "Activity Diagram":
            ActivityDiagramWindow(master, self.app, diagram_id=diag_id)
        elif diag.diag_type == "Block Diagram":
            BlockDiagramWindow(master, self.app, diagram_id=diag_id)
        elif diag.diag_type == "Internal Block Diagram":
            InternalBlockDiagramWindow(master, self.app, diagram_id=diag_id)

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
        elif item.startswith("obj_"):
            diag_id, oid = item[4:].split("_", 1)
            diag = self.repo.diagrams.get(diag_id)
            if diag:
                diag.objects = [o for o in diag.objects if str(o.get("obj_id")) != oid]
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

    # ------------------------------------------------------------------
    # Cut/Paste and Drag & Drop Handling
    # ------------------------------------------------------------------
    def cut(self):
        item = self.selected()
        if item:
            self.cut_item = item

    def paste(self):
        if not self.cut_item:
            return
        target = self.selected() or self.repo.root_package.elem_id
        if target.startswith("diag_"):
            target = self.repo.diagrams[target[5:]].package
        self._move_item(self.cut_item, target)
        self.cut_item = None
        self.populate()

    def on_drag_start(self, event):
        self.drag_item = self.tree.identify_row(event.y)

    def on_drag_motion(self, _event):
        pass

    def on_drag_release(self, event):
        if not self.drag_item:
            return
        target = self.tree.identify_row(event.y)
        if not target:
            self.drag_item = None
            return
        if target == self.drag_item:
            self.drag_item = None
            return
        region = self.tree.identify_region(event.x, event.y)
        if region in ("separator", "nothing"):
            parent = self.tree.parent(target)
            index = self.tree.index(target)
            self.tree.move(self.drag_item, parent, index)
            self._move_item(self.drag_item, parent)
        else:
            if target.startswith("diag_"):
                diag = self.repo.diagrams.get(target[5:])
                self._drop_on_diagram(self.drag_item, diag)
            else:
                self.tree.move(self.drag_item, target, "end")
                self._move_item(self.drag_item, target)
        self.drag_item = None
        self.populate()

    def _move_item(self, item, new_parent):
        if item.startswith("diag_"):
            self.repo.diagrams[item[5:]].package = new_parent
        else:
            self.repo.elements[item].owner = new_parent

    def _drop_on_diagram(self, elem_id, diagram):
        repo = self.repo
        # Dropping a diagram onto an Activity Diagram creates a referenced action
        if elem_id.startswith("diag_"):
            src_diag = repo.diagrams.get(elem_id[5:])
            if src_diag and diagram.diag_type == "Activity Diagram" and src_diag.diag_type in ("Activity Diagram", "Internal Block Diagram"):
                act = repo.create_element("Action Usage", name=src_diag.name, owner=diagram.package)
                repo.add_element_to_diagram(diagram.diag_id, act.elem_id)
                obj = SysMLObject(_get_next_id(), "Action Usage", 50.0, 50.0, element_id=act.elem_id, properties={"name": src_diag.name})
                diagram.objects.append(obj.__dict__)
                repo.link_diagram(act.elem_id, src_diag.diag_id)
                return
            messagebox.showerror("Drop Error", "This item cannot be dropped on that diagram.")
            return

        allowed = diagram.diag_type == "Block Diagram"
        if allowed and repo.elements[elem_id].elem_type == "Package":
            block = repo.create_element("Block", name=repo.elements[elem_id].name, owner=elem_id)
            repo.add_element_to_diagram(diagram.diag_id, block.elem_id)
            obj = SysMLObject(_get_next_id(), "Block", 50.0, 50.0, element_id=block.elem_id)
            diagram.objects.append(obj.__dict__)
        else:
            messagebox.showerror("Drop Error", "This item cannot be dropped on that diagram.")
