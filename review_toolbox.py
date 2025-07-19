import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
from dataclasses import dataclass, field
from typing import List

@dataclass
class ReviewParticipant:
    name: str
    email: str
    role: str  # 'reviewer' or 'approver'
    done: bool = False

@dataclass
class ReviewComment:
    comment_id: int
    node_id: int
    text: str
    reviewer: str
    target_type: str = "node"  # 'node', 'requirement', 'fmea', or 'fmea_field'
    req_id: str = ""
    field: str = ""
    resolved: bool = False
    resolution: str = ""

@dataclass
class ReviewData:
    name: str = ""
    description: str = ""
    mode: str = "peer"  # 'peer' or 'joint'
    participants: List[ReviewParticipant] = field(default_factory=list)
    comments: List[ReviewComment] = field(default_factory=list)
    fta_ids: List[int] = field(default_factory=list)
    fmea_names: List[str] = field(default_factory=list)
    approved: bool = False

class ParticipantDialog(simpledialog.Dialog):
    def __init__(self, parent, joint: bool):
        self.joint = joint
        self.participants: List[ReviewParticipant] = []
        super().__init__(parent, title="Review Participants")

    def body(self, master):
        self.row_frame = tk.Frame(master)
        self.row_frame.pack(fill=tk.BOTH, expand=True)
        btn = tk.Button(master, text="Add Participant", command=self.add_row)
        btn.pack(pady=5)
        self.add_row()

    def add_row(self):
        frame = tk.Frame(self.row_frame)
        frame.pack(fill=tk.X, pady=2)
        name = tk.Entry(frame, width=15)
        name.pack(side=tk.LEFT)
        email = tk.Entry(frame, width=20)
        email.pack(side=tk.LEFT, padx=5)
        if self.joint:
            role_cb = ttk.Combobox(frame, values=["reviewer", "approver"], state="readonly", width=10)
            role_cb.current(0)
            role_cb.pack(side=tk.LEFT, padx=5)
        else:
            role_cb = None
        self.participants.append((name, email, role_cb))

    def apply(self):
        result = []
        for name_entry, email_entry, role_cb in self.participants:
            name = name_entry.get().strip()
            if not name:
                continue
            email = email_entry.get().strip()
            role = role_cb.get() if role_cb else "reviewer"
            result.append(ReviewParticipant(name, email, role))
        self.result = result


class ReviewScopeDialog(simpledialog.Dialog):
    def __init__(self, parent, app):
        self.app = app
        super().__init__(parent, title="Select Review Scope")

    def body(self, master):
        tk.Label(master, text="FTAs:").grid(row=0, column=0, padx=5, pady=5)
        self.fta_list = tk.Listbox(master, selectmode=tk.MULTIPLE, height=6)
        self.fta_list.grid(row=1, column=0, padx=5, pady=5)
        for te in self.app.top_events:
            label = te.user_name or te.description or f"Node {te.unique_id}"
            self.fta_list.insert(tk.END, label)

        tk.Label(master, text="FMEAs:").grid(row=0, column=1, padx=5, pady=5)
        self.fmea_list = tk.Listbox(master, selectmode=tk.MULTIPLE, height=6)
        self.fmea_list.grid(row=1, column=1, padx=5, pady=5)
        for f in self.app.fmeas:
            self.fmea_list.insert(tk.END, f['name'])
        tk.Label(master, text="Hold Ctrl to select multiple").grid(row=2, column=0, columnspan=2, pady=(2,5))

    def apply(self):
        fta_ids = [self.app.top_events[i].unique_id for i in self.fta_list.curselection()]
        fmea_names = [self.app.fmeas[i]['name'] for i in self.fmea_list.curselection()]
        self.result = (fta_ids, fmea_names)

class ReviewToolbox(tk.Toplevel):
    def __init__(self, master, app):
        super().__init__(master)
        self.title("Review Toolbox")
        self.app = app
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        review_frame = tk.Frame(self)
        review_frame.pack(fill=tk.X)
        tk.Label(review_frame, text="Review:").pack(side=tk.LEFT)
        self.review_var = tk.StringVar()
        self.review_combo = ttk.Combobox(review_frame, textvariable=self.review_var,
                                         state="readonly")
        self.review_combo.pack(side=tk.LEFT, padx=5)
        self.review_combo.bind("<<ComboboxSelected>>", self.on_review_change)
        self.status_var = tk.StringVar()
        tk.Label(review_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=5)
        self.desc_var = tk.StringVar()
        tk.Label(self, textvariable=self.desc_var, wraplength=400, justify="left").pack(fill=tk.X, padx=5)

        user_frame = tk.Frame(self)
        user_frame.pack(fill=tk.X)
        tk.Label(user_frame, text="Current user:").pack(side=tk.LEFT)
        self.user_var = tk.StringVar(value=app.current_user)
        self.user_combo = ttk.Combobox(user_frame, textvariable=self.user_var,
                                       state="readonly")
        self.user_combo.pack(side=tk.LEFT, padx=5)
        self.user_combo.bind("<<ComboboxSelected>>", self.on_user_change)

        target_frame = tk.Frame(self)
        target_frame.pack(fill=tk.X)
        tk.Label(target_frame, text="Target:").pack(side=tk.LEFT)
        self.target_var = tk.StringVar()
        self.target_combo = ttk.Combobox(target_frame, textvariable=self.target_var,
                                         state="readonly")
        self.target_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.target_combo.bind("<<ComboboxSelected>>", self.on_target_change)

        self.comment_list = tk.Listbox(self, width=50)
        self.comment_list.pack(fill=tk.BOTH, expand=True)
        self.comment_list.bind("<<ListboxSelect>>", self.on_select)
        self.comment_list.bind("<Double-1>", self.open_comment)

        self.comment_display = tk.Text(self, height=4, state="disabled", wrap="word")
        self.comment_display.pack(fill=tk.X, padx=5, pady=5)

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X)
        tk.Button(btn_frame, text="Add Comment", command=self.add_comment).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Resolve", command=self.resolve_comment).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Mark Done", command=self.mark_done).pack(side=tk.LEFT)
        self.approve_btn = tk.Button(btn_frame, text="Approve", command=self.approve)
        self.approve_btn.pack(side=tk.LEFT)

        self.update_buttons()

        self.refresh_reviews()
        self.refresh_targets()
        self.refresh_comments()
        self.update_buttons()

    def on_close(self):
        self.app.review_window = None
        self.destroy()

    def refresh_reviews(self):
        names = [r.name for r in self.app.reviews]
        self.review_combo['values'] = names
        if self.app.review_data:
            self.review_var.set(self.app.review_data.name)
            self.status_var.set("approved" if self.app.review_data.approved else "open")
            self.desc_var.set(self.app.review_data.description)
        else:
            self.review_var.set("")
            self.status_var.set("")
            self.desc_var.set("")

    def on_review_change(self, event=None):
        name = self.review_var.get()
        for r in self.app.reviews:
            if r.name == name:
                self.app.review_data = r
                break
        self.status_var.set("approved" if self.app.review_data and self.app.review_data.approved else "open")
        if self.app.review_data:
            self.desc_var.set(self.app.review_data.description)
        else:
            self.desc_var.set("")
        self.refresh_comments()
        self.refresh_targets()
        self.update_buttons()
        try:
            if hasattr(self.app, "canvas") and self.app.canvas.winfo_exists():
                self.app.redraw_canvas()
        except tk.TclError:
            pass

    def refresh_comments(self):
        self.comment_list.delete(0, tk.END)
        if not self.app.review_data:
            return
        self.user_combo['values'] = [p.name for p in self.app.review_data.participants]
        if self.app.current_user:
            self.user_var.set(self.app.current_user)
        for c in self.app.review_data.comments:
            node = self.app.find_node_by_id_all(c.node_id)
            node_name = node.name if node else f"ID {c.node_id}"
            if c.target_type == "requirement" and c.req_id:
                node_name += f" [Req {c.req_id}]"
            elif c.target_type == "fmea":
                node_name += " [FMEA]"
            elif c.target_type == "fmea_field" and c.field:
                node_name += f" [FMEA {c.field}]"

            status = "(resolved)" if c.resolved else ""
            self.comment_list.insert(tk.END, f"{c.comment_id}: {node_name} - {c.reviewer} {status}")
        self.update_buttons()

    def on_select(self, event):
        if not self.app.review_data:
            return
        selection = self.comment_list.curselection()
        if selection:
            c = self.app.review_data.comments[selection[0]]
            node = self.app.find_node_by_id_all(c.node_id)
            if node:
                self.app.focus_on_node(node)
            self.show_comment(c)

    def add_comment(self):
        target = self.app.comment_target
        if not target:
            label = self.target_var.get()
            if label:
                target = self.target_map.get(label)
        if not target and not self.app.selected_node:
            messagebox.showwarning("Add Comment", "Select a node first")
            return
        reviewer = self.app.current_user
        text = simpledialog.askstring("Comment", "Enter comment:")
        if not text:
            return
        comment_id = len(self.app.review_data.comments) + 1
        if target and target[0] == "requirement":
            node_id = target[1]
            c = ReviewComment(comment_id, node_id, text, reviewer, target_type="requirement", req_id=target[2])
        elif target and target[0] == "fmea":
            node_id = target[1]
            c = ReviewComment(comment_id, node_id, text, reviewer, target_type="fmea")
        elif target and target[0] == "fmea_field":
            node_id = target[1]
            c = ReviewComment(comment_id, node_id, text, reviewer,
                             target_type="fmea_field", field=target[2])

        elif target and target[0] == "node":
            node_id = target[1]
            c = ReviewComment(comment_id, node_id, text, reviewer)
        else:
            c = ReviewComment(comment_id, self.app.selected_node.unique_id, text, reviewer)
        self.app.review_data.comments.append(c)
        self.app.comment_target = None
        self.refresh_comments()

    def resolve_comment(self):
        idx = self.comment_list.curselection()
        if not idx:
            return
        c = self.app.review_data.comments[idx[0]]
        resolution = simpledialog.askstring("Resolve Comment", "Enter resolution comment:")
        if resolution is None:
            return
        c.resolved = True
        c.resolution = resolution
        self.refresh_comments()

    def mark_done(self):
        user = self.app.current_user
        for p in self.app.review_data.participants:
            if p.name == user:
                p.done = True
        messagebox.showinfo("Review", "Marked as done")
        self.update_buttons()

    def approve(self):
        if self.app.review_data.mode == 'joint':
            all_done = all(p.done for p in self.app.review_data.participants if p.role == 'reviewer')
            if not all_done:
                messagebox.showwarning("Approve", "Not all reviewers are done")
                return
        unresolved = [c for c in self.app.review_data.comments if not c.resolved]
        if unresolved:
            messagebox.showwarning("Approve", "There are unresolved comments")
            return
        self.app.review_data.approved = True
        messagebox.showinfo("Approve", "Review approved")
        self.app.add_version()
        self.refresh_reviews()

    def open_comment(self, event):
        selection = self.comment_list.curselection()
        if not selection:
            return
        c = self.app.review_data.comments[selection[0]]
        self.show_comment(c)

    def on_user_change(self, event):
        self.app.current_user = self.user_var.get()
        self.update_buttons()

    def show_comment(self, comment):
        self.comment_display.config(state="normal")
        self.comment_display.delete("1.0", tk.END)
        text = comment.text
        if comment.resolution:
            text += f"\n\nResolution: {comment.resolution}"
        self.comment_display.insert("1.0", text)
        self.comment_display.config(state="disabled")

    def update_buttons(self):
        role = None
        for p in (self.app.review_data.participants if self.app.review_data else []):
            if p.name == self.app.current_user:
                role = p.role
                break
        if self.app.review_data and self.app.review_data.mode == 'joint' and role == 'approver':
            self.approve_btn.pack(side=tk.LEFT)
        else:
            self.approve_btn.pack_forget()

    def refresh_targets(self):
        items, self.target_map = self.app.get_review_targets()
        self.target_combo['values'] = items
        if items:
            self.target_var.set(items[0])

    def on_target_change(self, event=None):
        label = self.target_var.get()
        target = self.target_map.get(label)
        self.app.comment_target = None
        if not target:
            return
        node = self.app.find_node_by_id_all(target[1]) if len(target) > 1 else None
        if node:
            self.app.selected_node = node
            self.app.focus_on_node(node)
        if target[0] == 'requirement':
            self.app.comment_target = ('requirement', target[2])
        elif target[0] == 'fmea':
            self.app.comment_target = ('fmea', target[1])

class ReviewDocumentDialog(tk.Toplevel):
    def __init__(self, master, app, review):
        super().__init__(master)
        self.app = app
        self.review = review
        self.title(f"Review Document - {review.name}")

        self.outer = tk.Canvas(self)
        vbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.outer.yview)
        self.outer.configure(yscrollcommand=vbar.set)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.outer.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.inner = tk.Frame(self.outer)
        self.outer.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind(
            "<Configure>",
            lambda e: self.outer.configure(scrollregion=self.outer.bbox("all")),
        )
        self.populate()

    def draw_tree(self, canvas, node):
        def draw_connections(n):
            region_width = 100
            parent_bottom = (n.x, n.y + 40)
            for i, ch in enumerate(n.children):
                parent_conn = (
                    n.x - region_width / 2 + (i + 0.5) * (region_width / len(n.children)),
                    parent_bottom[1],
                )
                child_top = (ch.x, ch.y - 45)
                fta_drawing_helper.draw_90_connection(
                    canvas, parent_conn, child_top, outline_color="dimgray", line_width=1
                )
                draw_connections(ch)

        def draw_node_simple(n):
            fill = self.app.get_node_fill_color(n)
            eff_x, eff_y = n.x, n.y
            top_text = n.node_type
            if n.input_subtype:
                top_text += f" ({n.input_subtype})"
            if n.description:
                top_text += f"\n{n.description}"
            bottom_text = n.name
            typ = n.node_type.upper()
            if n.is_page:
                fta_drawing_helper.draw_triangle_shape(
                    canvas,
                    eff_x,
                    eff_y,
                    scale=40,
                    top_text=top_text,
                    bottom_text=bottom_text,
                    fill=fill,
                    outline_color="dimgray",
                    line_width=1,
                )
            elif typ in ["GATE", "RIGOR LEVEL", "TOP EVENT"]:
                if n.gate_type and n.gate_type.upper() == "OR":
                    fta_drawing_helper.draw_rotated_or_gate_shape(
                        canvas,
                        eff_x,
                        eff_y,
                        scale=40,
                        top_text=top_text,
                        bottom_text=bottom_text,
                        fill=fill,
                        outline_color="dimgray",
                        line_width=1,
                    )
                else:
                    fta_drawing_helper.draw_rotated_and_gate_shape(
                        canvas,
                        eff_x,
                        eff_y,
                        scale=40,
                        top_text=top_text,
                        bottom_text=bottom_text,
                        fill=fill,
                        outline_color="dimgray",
                        line_width=1,
                    )
            else:
                fta_drawing_helper.draw_circle_event_shape(
                    canvas,
                    eff_x,
                    eff_y,
                    45,
                    top_text=top_text,
                    bottom_text=bottom_text,
                    fill=fill,
                    outline_color="dimgray",
                    line_width=1,
                )

        def draw_all(n):
            draw_node_simple(n)
            for ch in n.children:
                draw_all(ch)

        canvas.delete("all")
        draw_connections(node)
        draw_all(node)
        canvas.config(scrollregion=canvas.bbox("all"))

    def populate(self):
        row = 0
        heading_font = ("TkDefaultFont", 10, "bold")
        for nid in self.review.fta_ids:
            node = self.app.find_node_by_id_all(nid)
            if not node:
                continue
            tk.Label(self.inner, text=f"FTA: {node.name}", font=heading_font).grid(
                row=row, column=0, sticky="w", padx=5, pady=5
            )
            row += 1
            c = tk.Canvas(self.inner, width=600, height=400, bg="white")
            c.grid(row=row, column=0, padx=5, pady=5)
            self.draw_tree(c, node)
            row += 1
        for name in self.review.fmea_names:
            fmea = next((f for f in self.app.fmeas if f["name"] == name), None)
            if not fmea:
                continue
            tk.Label(self.inner, text=f"FMEA: {name}", font=heading_font).grid(
                row=row, column=0, sticky="w", padx=5, pady=5
            )
            row += 1
            text = tk.Text(self.inner, height=10, wrap="word")
            text.grid(row=row, column=0, sticky="nsew", padx=5, pady=5)
            for entry in fmea["entries"]:
                label = entry.description or entry.user_name or f"BE {entry.unique_id}"
                rpn = entry.fmea_severity * entry.fmea_occurrence * entry.fmea_detection
                text.insert(tk.END, f"Failure Mode: {label}\nRPN: {rpn}\n\n")
            text.config(state="disabled")
            row += 1

class VersionCompareDialog(tk.Toplevel):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.title("Compare Versions")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        names = [v["name"] for v in self.app.versions]
        tk.Label(self, text="Base version:").pack(padx=5, pady=2)
        self.base_var = tk.StringVar()
        self.base_combo = ttk.Combobox(self, values=names, textvariable=self.base_var, state="readonly")
        self.base_combo.pack(fill=tk.X, padx=5)

        tk.Label(self, text="Compare with:").pack(padx=5, pady=2)
        self.other_var = tk.StringVar()
        self.other_combo = ttk.Combobox(self, values=names, textvariable=self.other_var, state="readonly")
        self.other_combo.pack(fill=tk.X, padx=5)
        self.other_combo.bind("<<ComboboxSelected>>", self.compare)

        self.diff_text = tk.Text(self, width=60, height=20)
        self.diff_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.diff_text.tag_config('change', foreground='red')

    def compare(self, event=None):
        base = self.base_var.get()
        other = self.other_var.get()
        if not base or not other:
            return
        data1 = data2 = None
        for v in self.app.versions:
            if v["name"] == base:
                data1 = v["data"]
            if v["name"] == other:
                data2 = v["data"]
        if data1 is None or data2 is None:
            return
        changed = self.app.calculate_diff_between(data1, data2)
        self.diff_text.delete("1.0", tk.END)
        for nid in changed:
            node = self.app.find_node_by_id_all(nid)
            label = node.name if node else f"Node {nid}"
            self.diff_text.insert(tk.END, label + "\n", "change")
        self.app.diff_nodes = changed
        try:
            if hasattr(self.app, "canvas") and self.app.canvas.winfo_exists():
                self.app.redraw_canvas()
        except tk.TclError:
            pass

    def on_close(self):
        self.app.diff_nodes = []
        try:
            if hasattr(self.app, "canvas") and self.app.canvas.winfo_exists():
                self.app.redraw_canvas()
        except tk.TclError:
            pass
        self.destroy()
