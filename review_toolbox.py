import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
from dataclasses import dataclass
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
    resolved: bool = False

@dataclass
class ReviewData:
    mode: str  # 'peer' or 'joint'
    participants: List[ReviewParticipant]
    comments: List[ReviewComment]
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

class ReviewToolbox(tk.Toplevel):
    def __init__(self, master, app):
        super().__init__(master)
        self.title("Review Toolbox")
        self.app = app
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        user_frame = tk.Frame(self)
        user_frame.pack(fill=tk.X)
        tk.Label(user_frame, text="Current user:").pack(side=tk.LEFT)
        self.user_var = tk.StringVar(value=app.current_user)
        self.user_combo = ttk.Combobox(user_frame, textvariable=self.user_var,
                                       state="readonly")
        self.user_combo.pack(side=tk.LEFT, padx=5)
        self.user_combo.bind("<<ComboboxSelected>>", self.on_user_change)

        self.comment_list = tk.Listbox(self, width=50)
        self.comment_list.pack(fill=tk.BOTH, expand=True)
        self.comment_list.bind("<<ListboxSelect>>", self.on_select)
        self.comment_list.bind("<Double-1>", self.open_comment)

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X)
        tk.Button(btn_frame, text="Add Comment", command=self.add_comment).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Resolve", command=self.resolve_comment).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Mark Done", command=self.mark_done).pack(side=tk.LEFT)
        self.approve_btn = tk.Button(btn_frame, text="Approve", command=self.approve)
        self.approve_btn.pack(side=tk.LEFT)

        self.update_buttons()

        self.refresh_comments()
        self.update_buttons()

    def on_close(self):
        self.app.review_window = None
        self.destroy()

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

    def add_comment(self):
        if not self.app.selected_node:
            messagebox.showwarning("Add Comment", "Select a node first")
            return
        reviewer = self.app.current_user
        text = simpledialog.askstring("Comment", "Enter comment:")
        if not text:
            return
        comment_id = len(self.app.review_data.comments) + 1
        c = ReviewComment(comment_id, self.app.selected_node.unique_id, text, reviewer)
        self.app.review_data.comments.append(c)
        self.refresh_comments()

    def resolve_comment(self):
        idx = self.comment_list.curselection()
        if not idx:
            return
        c = self.app.review_data.comments[idx[0]]
        c.resolved = True
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

    def open_comment(self, event):
        selection = self.comment_list.curselection()
        if not selection:
            return
        c = self.app.review_data.comments[selection[0]]
        messagebox.showinfo(f"Comment {c.comment_id}", c.text)

    def on_user_change(self, event):
        self.app.current_user = self.user_var.get()
        self.update_buttons()

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
