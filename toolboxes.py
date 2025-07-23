import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import csv
import copy
from models import ReliabilityComponent, ReliabilityAnalysis, HazopEntry, HaraEntry, QUALIFICATIONS, COMPONENT_ATTR_TEMPLATES, RELIABILITY_MODELS, calc_asil

class ReliabilityWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title("Reliability Analysis")
        self.geometry("600x400")
        self.components = []

        ttk.Label(self, text="Standard:").pack(anchor="w")
        self.standard_var = tk.StringVar(value="IEC 62380")
        ttk.Combobox(
            self,
            textvariable=self.standard_var,
            values=["IEC 62380", "SN 29500"],
            state="readonly",
        ).pack(anchor="w")

        ttk.Label(self, text="Mission Profile:").pack(anchor="w")
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(
            self,
            textvariable=self.profile_var,
            values=[mp.name for mp in app.mission_profiles],
            state="readonly",
        )
        self.profile_combo.pack(anchor="w", fill="x")

        self.tree = ttk.Treeview(
            self,
            columns=("name", "type", "qty", "fit", "qualification"),
            show="headings",
        )
        for col in ("name", "type", "qty", "fit", "qualification"):
            heading = "Qualification" if col == "qualification" else col.capitalize()
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=120 if col == "qualification" else 100)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.show_formula)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Load CSV", command=self.load_csv).pack(
            side=tk.LEFT, padx=2, pady=2
        )
        ttk.Button(btn_frame, text="Add Component", command=self.add_component).pack(
            side=tk.LEFT, padx=2, pady=2
        )
        ttk.Button(btn_frame, text="Add Circuit", command=self.add_circuit).pack(
            side=tk.LEFT, padx=2, pady=2
        )
        ttk.Button(btn_frame, text="Configure Component", command=self.configure_component).pack(
            side=tk.LEFT, padx=2, pady=2
        )
        ttk.Button(btn_frame, text="Calculate FIT", command=self.calculate_fit).pack(
            side=tk.LEFT, padx=2, pady=2
        )
        ttk.Button(btn_frame, text="Save Analysis", command=self.save_analysis).pack(
            side=tk.LEFT, padx=2, pady=2
        )
        ttk.Button(btn_frame, text="Load Analysis", command=self.load_analysis).pack(
            side=tk.LEFT, padx=2, pady=2
        )
        self.formula_label = ttk.Label(self, text="")
        self.formula_label.pack(anchor="w", padx=5, pady=5)

    def add_component(self):
        dialog = tk.Toplevel(self)
        dialog.title("New Component")
        ttk.Label(dialog, text="Name").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(dialog, text="Type").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        type_var = tk.StringVar(value="capacitor")
        ttk.Combobox(dialog, textvariable=type_var, values=list(COMPONENT_ATTR_TEMPLATES.keys()), state="readonly").grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(dialog, text="Quantity").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        qty_var = tk.IntVar(value=1)
        ttk.Entry(dialog, textvariable=qty_var).grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(dialog, text="Qualification").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        qual_var = tk.StringVar(value="None")
        ttk.Combobox(dialog, textvariable=qual_var, values=QUALIFICATIONS, state="readonly").grid(row=3, column=1, padx=5, pady=5)
        passive_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(dialog, text="Passive", variable=passive_var).grid(row=4, column=0, columnspan=2, pady=5)

        def ok():
            comp = ReliabilityComponent(
                name_var.get(),
                type_var.get(),
                qty_var.get(),
                {},
                qual_var.get(),
                is_passive=passive_var.get(),
            )
            template = COMPONENT_ATTR_TEMPLATES.get(comp.comp_type, {})
            for k, v in template.items():
                comp.attributes[k] = v[0] if isinstance(v, list) else v
            self.components.append(comp)
            self.refresh_tree()
            dialog.destroy()

        ttk.Button(dialog, text="Add", command=ok).grid(row=5, column=0, columnspan=2, pady=5)
        dialog.grab_set()
        dialog.wait_window()

    def add_circuit(self):
        dlg = tk.Toplevel(self)
        dlg.title("New Circuit")
        ttk.Label(dlg, text="Name").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        name_var = tk.StringVar()
        ttk.Entry(dlg, textvariable=name_var).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(dlg, text="BOMs").grid(row=1, column=0, padx=5, pady=5, sticky="ne")
        lb = tk.Listbox(dlg, selectmode=tk.MULTIPLE, height=6)
        for ra in self.app.reliability_analyses:
            lb.insert(tk.END, ra.name)
        lb.grid(row=1, column=1, padx=5, pady=5)
        qty_var = tk.IntVar(value=1)
        ttk.Label(dlg, text="Quantity").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(dlg, textvariable=qty_var).grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(dlg, text="Qualification").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        qual_var = tk.StringVar(value="None")
        ttk.Combobox(dlg, textvariable=qual_var, values=QUALIFICATIONS, state="readonly").grid(row=3, column=1, padx=5, pady=5)
        passive_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(dlg, text="Passive", variable=passive_var).grid(row=4, column=0, columnspan=2, pady=5)

        def ok():
            bom_idxs = lb.curselection()
            boms = [self.app.reliability_analyses[i].components for i in bom_idxs]
            comp = ReliabilityComponent(
                name_var.get(),
                "circuit",
                qty_var.get(),
                {},
                qual_var.get(),
                is_passive=passive_var.get(),
            )
            comp.sub_boms = copy.deepcopy(boms)
            comp.fit = 0.0
            self.components.append(comp)
            self.refresh_tree()
            dlg.destroy()

        ttk.Button(dlg, text="Add", command=ok).grid(row=5, column=0, columnspan=2, pady=5)
        dlg.grab_set()
        dlg.wait_window()

    def show_formula(self, event=None):
        sel = self.tree.focus()
        if not sel:
            self.formula_label.config(text="")
            return
        idx = self.tree.index(sel)
        if idx >= len(self.components):
            return
        comp = self.components[idx]
        std = self.standard_var.get()
        info = RELIABILITY_MODELS.get(std, {}).get(comp.comp_type)
        if info:
            self.formula_label.config(text=f"Formula: {info['text']}")
        else:
            self.formula_label.config(text="Formula: N/A")

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for comp in self.components:
            self.tree.insert(
                "",
                "end",
                values=(
                    comp.name,
                    comp.comp_type,
                    comp.quantity,
                    f"{comp.fit:.2f}",
                    comp.qualification,
                ),
            )
        self.profile_combo.config(values=[mp.name for mp in self.app.mission_profiles])

    def load_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not path:
            return
        self.components.clear()
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            fields = reader.fieldnames or []
            mapping = self.ask_mapping(fields)
            if not mapping:
                return
            for row in reader:
                try:
                    name = row.get(mapping["name"], "")
                    ctype = row.get(mapping["type"], "")
                    qty = int(row.get(mapping["qty"], 1) or 1)
                    qual = row.get(mapping.get("qualification"), "") if mapping.get("qualification") else ""
                    comp = ReliabilityComponent(name, ctype, qty, {}, qual)
                    template = COMPONENT_ATTR_TEMPLATES.get(ctype, {})
                    for k, v in template.items():
                        comp.attributes[k] = v[0] if isinstance(v, list) else v
                    # store any extra columns as attributes
                    for key, val in row.items():
                        if key not in mapping.values():
                            comp.attributes[key] = val
                    self.components.append(comp)
                except Exception:
                    continue
        self.refresh_tree()

    def ask_mapping(self, fields):
        if not fields:
            return None
        win = tk.Toplevel(self)
        win.title("Map Columns")
        vars = {}
        targets = ["name", "type", "qty", "qualification"]
        for i, tgt in enumerate(targets):
            ttk.Label(win, text=tgt.capitalize()).grid(row=i, column=0, padx=5, pady=5, sticky="e")
            var = tk.StringVar()
            cb = ttk.Combobox(win, textvariable=var, values=fields, state="readonly")
            if i < len(fields):
                var.set(fields[i])
            cb.grid(row=i, column=1, padx=5, pady=5)
            vars[tgt] = var

        result = {}

        def ok():
            for k, v in vars.items():
                result[k] = v.get()
            win.destroy()

        def cancel():
            result.clear()
            win.destroy()

        ttk.Button(win, text="OK", command=ok).grid(row=len(targets), column=0, pady=5)
        ttk.Button(win, text="Cancel", command=cancel).grid(row=len(targets), column=1, pady=5)
        win.grab_set()
        win.wait_window()
        if not result:
            return None
        return result

    def configure_component(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showwarning("Configure", "Select a component")
            return
        idx = self.tree.index(sel)
        comp = self.components[idx]

        template = COMPONENT_ATTR_TEMPLATES.get(comp.comp_type, {})
        for k, v in template.items():
            comp.attributes.setdefault(k, v[0] if isinstance(v, list) else v)

        class ParamDialog(simpledialog.Dialog):
            def body(self, master):
                self.vars = {}
                row = 0
                ttk.Label(master, text="Quantity").grid(row=row, column=0, padx=5, pady=5, sticky="e")
                qty_var = tk.IntVar(value=comp.quantity)
                ttk.Entry(master, textvariable=qty_var).grid(row=row, column=1, padx=5, pady=5)
                self.vars["__qty__"] = qty_var
                row += 1
                ttk.Label(master, text="Qualification").grid(row=row, column=0, padx=5, pady=5, sticky="e")
                qual_var = tk.StringVar(value=comp.qualification)
                ttk.Combobox(master, textvariable=qual_var, values=QUALIFICATIONS, state="readonly").grid(row=row, column=1, padx=5, pady=5)
                self.vars["__qual__"] = qual_var
                row += 1
                for k, v in comp.attributes.items():
                    ttk.Label(master, text=k).grid(row=row, column=0, padx=5, pady=5, sticky="e")
                    if isinstance(template.get(k), list):
                        var = tk.StringVar(value=str(v))
                        ttk.Combobox(master, textvariable=var, values=template[k], state="readonly").grid(row=row, column=1, padx=5, pady=5)
                    else:
                        var = tk.StringVar(value=str(v))
                        ttk.Entry(master, textvariable=var).grid(row=row, column=1, padx=5, pady=5)
                    self.vars[k] = var
                    row += 1

            def apply(self):
                comp.quantity = int(self.vars["__qty__"].get())
                comp.qualification = self.vars["__qual__"].get()
                for k, v in self.vars.items():
                    if k.startswith("__"):
                        continue
                    comp.attributes[k] = v.get()

        ParamDialog(self)
        self.refresh_tree()

    def calculate_fit(self):
        prof_name = self.profile_var.get()
        mp = next((m for m in self.app.mission_profiles if m.name == prof_name), None)
        if mp is None:
            messagebox.showwarning("FIT", "Select a mission profile")
            return
        std = self.standard_var.get()
        total = 0.0
        for comp in self.components:
            if comp.sub_boms:
                sub_total = 0.0
                for bom in comp.sub_boms:
                    for sub in bom:
                        info = RELIABILITY_MODELS.get(std, {}).get(sub.comp_type)
                        if info:
                            sub.fit = info["formula"](sub.attributes, mp) * mp.tau
                        else:
                            sub.fit = 0.0
                        sub_total += sub.fit * sub.quantity
                comp.fit = sub_total
            else:
                info = RELIABILITY_MODELS.get(std, {}).get(comp.comp_type)
                if info:
                    comp.fit = info["formula"](comp.attributes, mp) * mp.tau
                else:
                    comp.fit = 0.0
            total += comp.fit * comp.quantity

        comp_fit = {c.name: c.fit * c.quantity for c in self.components}
        spf = 0.0
        lpf = 0.0
        total_modes = 0.0
        for be in self.app.fmea_entries:
            comp_name = (
                be.parents[0].user_name if be.parents else getattr(be, "fmea_component", "")
            )
            fit = comp_fit.get(comp_name, 0.0)
            frac = be.fmeda_fault_fraction
            if frac > 1.0:
                frac /= 100.0
            fit_mode = fit * frac
            total_modes += fit_mode
            if be.fmeda_fault_type == "permanent":
                spf += fit_mode * (1 - be.fmeda_diag_cov)
            else:
                lpf += fit_mode * (1 - be.fmeda_diag_cov)
        dc = 1 - (spf + lpf) / total_modes if total_modes else 0.0
        self.app.reliability_components = list(self.components)
        self.app.reliability_total_fit = total_modes
        self.app.spfm = spf
        self.app.lpfm = lpf
        self.app.reliability_dc = dc
        self.refresh_tree()
        self.formula_label.config(
            text=f"Total FIT: {total_modes:.2f}  DC: {dc:.2f}  SPFM: {spf:.2f}  LPFM: {lpf:.2f}"
        )

    def save_analysis(self):
        if not self.components:
            messagebox.showwarning("Save", "No components defined")
            return
        name = simpledialog.askstring("Save Analysis", "Enter analysis name:")
        if not name:
            return
        ra = ReliabilityAnalysis(
            name,
            self.standard_var.get(),
            self.profile_var.get(),
            copy.deepcopy(self.components),
            self.app.reliability_total_fit,
            self.app.spfm,
            self.app.lpfm,
            self.app.reliability_dc,
        )
        self.app.reliability_analyses.append(ra)
        messagebox.showinfo("Save", "Analysis saved")

    def load_analysis(self):
        """Load a previously saved reliability analysis."""
        if not self.app.reliability_analyses:
            messagebox.showwarning("Load", "No saved analyses")
            return
        win = tk.Toplevel(self)
        win.title("Select Analysis")
        lb = tk.Listbox(win, height=8, width=40)
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        for ra in self.app.reliability_analyses:
            lb.insert(tk.END, ra.name)

        def do_load():
            sel = lb.curselection()
            if not sel:
                return
            ra = self.app.reliability_analyses[sel[0]]
            self.standard_var.set(ra.standard)
            self.profile_var.set(ra.profile)
            self.components = copy.deepcopy(ra.components)
            self.app.reliability_total_fit = ra.total_fit
            self.app.spfm = ra.spfm
            self.app.lpfm = ra.lpfm
            self.app.reliability_dc = ra.dc
            win.destroy()
            self.refresh_tree()
            self.formula_label.config(
                text=f"Total FIT: {ra.total_fit:.2f}  DC: {ra.dc:.2f}  SPFM: {ra.spfm:.2f}  LPFM: {ra.lpfm:.2f}"
            )

        ttk.Button(win, text="Load", command=do_load).pack(side=tk.RIGHT, padx=5, pady=5)


class FI2TCWindow(tk.Toplevel):
    COLS = [
        "id","system_function","allocation","interfaces","insufficiency",
        "scene","scenario","driver_behavior","occurrence","vehicle_effect",
        "severity","design_measures","verification","measure_effectiveness",
        "triggering_condition","worst_case","tc_effect","mitigation","acceptance"
    ]
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title("FI2TC Analysis")
        self.tree = ttk.Treeview(self, columns=self.COLS, show="headings")
        for c in self.COLS:
            self.tree.heading(c, text=c.replace("_"," ").title())
            self.tree.column(c, width=120)
        self.tree.pack(fill=tk.BOTH, expand=True)
        btn = ttk.Frame(self)
        btn.pack()
        ttk.Button(btn, text="Add", command=self.add_row).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(btn, text="Edit", command=self.edit_row).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(btn, text="Delete", command=self.del_row).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(btn, text="Export CSV", command=self.export_csv).pack(side=tk.LEFT, padx=2, pady=2)
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for row in self.app.fi2tc_entries:
            self.tree.insert("", "end", values=[row.get(k, "") for k in self.COLS])

    class RowDialog(simpledialog.Dialog):
        def __init__(self, parent, app, data=None):
            self.app = app
            self.parent_win = parent
            default = {k: "" for k in parent.COLS}
            self.data = data or default
            super().__init__(parent, title="Edit Row")
        def body(self, master):
            fi_names = [n.user_name or f"FI {n.unique_id}" for n in self.app.get_all_functional_insufficiencies()]
            tc_names = [n.user_name or f"TC {n.unique_id}" for n in self.app.get_all_triggering_conditions()]
            func_names = self.app.get_all_function_names()
            comp_names = self.app.get_all_component_names()
            scen_names = self.app.get_all_scenario_names()
            scene_names = self.app.get_all_scenery_names()
            self.widgets = {}
            r = 0

            def refresh_funcs(*_):
                comp = self.widgets.get("allocation")
                if isinstance(comp, tk.StringVar):
                    func_opts = sorted({e.function for e in self.app.hazop_entries if not comp.get() or e.component == comp.get()})
                else:
                    func_opts = func_names
                if "system_function" in self.widgets:
                    w = self.widgets["system_function_widget"]
                    w["values"] = func_opts

            for col in self.parent_win.COLS:
                ttk.Label(master, text=col.replace("_", " ").title()).grid(row=r, column=0, sticky="e")
                if col == "triggering_condition":
                    var = tk.StringVar(value=self.data.get(col, ""))
                    cb = ttk.Combobox(master, textvariable=var, values=tc_names, state="readonly")
                    cb.grid(row=r, column=1)
                    self.widgets[col] = var
                elif col == "insufficiency":
                    var = tk.StringVar(value=self.data.get(col, ""))
                    cb = ttk.Combobox(master, textvariable=var, values=fi_names, state="readonly")
                    cb.grid(row=r, column=1)
                    self.widgets[col] = var
                elif col == "system_function":
                    var = tk.StringVar(value=self.data.get(col, ""))
                    cb = ttk.Combobox(master, textvariable=var, values=func_names, state="readonly")
                    cb.grid(row=r, column=1)
                    self.widgets[col] = var
                    self.widgets["system_function_widget"] = cb
                elif col == "allocation":
                    var = tk.StringVar(value=self.data.get(col, ""))
                    cb = ttk.Combobox(master, textvariable=var, values=comp_names, state="readonly")
                    cb.grid(row=r, column=1)
                    cb.bind("<<ComboboxSelected>>", refresh_funcs)
                    self.widgets[col] = var
                elif col == "scene":
                    var = tk.StringVar(value=self.data.get(col, ""))
                    cb = ttk.Combobox(master, textvariable=var, values=scene_names, state="readonly")
                    cb.grid(row=r, column=1)
                    self.widgets[col] = var
                elif col == "scenario":
                    var = tk.StringVar(value=self.data.get(col, ""))
                    cb = ttk.Combobox(master, textvariable=var, values=scen_names, state="readonly")
                    cb.grid(row=r, column=1)
                    self.widgets[col] = var
                elif col == "severity":
                    var = tk.StringVar(value=self.data.get(col, ""))
                    cb = ttk.Combobox(master, textvariable=var, values=["1", "2", "3"], state="readonly")
                    cb.grid(row=r, column=1)
                    self.widgets[col] = var
                else:
                    ent = tk.Entry(master)
                    ent.insert(0, self.data.get(col, ""))
                    ent.grid(row=r, column=1)
                    self.widgets[col] = ent
                r += 1
            refresh_funcs()
        def apply(self):
            for col, widget in self.widgets.items():
                if isinstance(widget, tk.Entry):
                    self.data[col] = widget.get()
                else:
                    self.data[col] = widget.get()

    def add_row(self):
        dlg = self.RowDialog(self, self.app)
        self.app.fi2tc_entries.append(dlg.data)
        self.refresh()
    def edit_row(self):
        sel = self.tree.focus()
        if not sel:
            return
        idx = self.tree.index(sel)
        data = self.app.fi2tc_entries[idx]
        dlg = self.RowDialog(self, self.app, data)
        self.refresh()
    def del_row(self):
        sel = self.tree.selection()
        for iid in sel:
            idx = self.tree.index(iid)
            if idx < len(self.app.fi2tc_entries):
                del self.app.fi2tc_entries[idx]
        self.refresh()
    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")])
        if not path:
            return
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(self.COLS)
            for r in self.app.fi2tc_entries:
                w.writerow([r.get(k, "") for k in self.COLS])
        messagebox.showinfo("Export", "FI2TC exported")

class HazopWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title("HAZOP Analysis")
        self.geometry("600x400")

        columns = ("function", "malfunction", "type", "safety", "rationale")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
            if col in ("rationale", "hazard"):
                width = 200
            else:
                width = 120
            self.tree.column(col, width=width)
        self.tree.pack(fill=tk.BOTH, expand=True)

        btn = ttk.Frame(self)
        btn.pack(fill=tk.X)
        ttk.Button(btn, text="Add", command=self.add_row).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(btn, text="Edit", command=self.edit_row).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(btn, text="Delete", command=self.del_row).pack(side=tk.LEFT, padx=2, pady=2)

        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for row in self.app.hazop_entries:
            vals = [
                row.function,
                row.malfunction,
                row.mtype,
                row.scenario,
                row.conditions,
                row.hazard,
                "Yes" if row.safety else "No",
                row.rationale,
                "Yes" if row.covered else "No",
                row.covered_by,
            ]
            self.tree.insert("", "end", values=vals)

    class RowDialog(simpledialog.Dialog):
        def __init__(self, parent, row=None):
            self.app = parent.app
            self.row = row or HazopEntry(
                "",
                "",
                "No/Not",
                "",
                "",
                "",
                False,
                "",
                False,
                "",
            )
            super().__init__(parent, title="Edit HAZOP Row")

        def body(self, master):
            ttk.Label(master, text="Function").grid(row=0, column=0, sticky="e", padx=5, pady=5)
            self.func = tk.StringVar(value=self.row.function)
            ttk.Entry(master, textvariable=self.func).grid(row=0, column=1, padx=5, pady=5)

            ttk.Label(master, text="Malfunction").grid(row=1, column=0, sticky="e", padx=5, pady=5)
            self.mal = tk.StringVar(value=self.row.malfunction)
            ttk.Entry(master, textvariable=self.mal).grid(row=1, column=1, padx=5, pady=5)

            ttk.Label(master, text="Type").grid(row=2, column=0, sticky="e", padx=5, pady=5)
            self.typ = tk.StringVar(value=self.row.mtype)
            ttk.Combobox(
                master,
                textvariable=self.typ,
                values=["No/Not", "Unintended", "Excessive", "Insufficient", "Reverse"],
                state="readonly",
            ).grid(row=2, column=1, padx=5, pady=5)

            ttk.Label(master, text="Scenario").grid(row=3, column=0, sticky="e", padx=5, pady=5)
            scenarios = []
            for lib in self.app.scenario_libraries:
                scenarios.extend(lib.get("scenarios", []))
            self.scen = tk.StringVar(value=self.row.scenario)
            ttk.Combobox(master, textvariable=self.scen, values=scenarios, state="readonly").grid(row=3, column=1, padx=5, pady=5)

            ttk.Label(master, text="Driving Conditions").grid(row=4, column=0, sticky="e", padx=5, pady=5)
            self.cond = tk.StringVar(value=self.row.conditions)
            ttk.Entry(master, textvariable=self.cond).grid(row=4, column=1, padx=5, pady=5)

            ttk.Label(master, text="Hazard").grid(row=5, column=0, sticky="ne", padx=5, pady=5)
            self.haz = tk.Text(master, width=30, height=3)
            self.haz.insert("1.0", self.row.hazard)
            self.haz.grid(row=5, column=1, padx=5, pady=5)

            ttk.Label(master, text="Safety Relevant").grid(row=6, column=0, sticky="e", padx=5, pady=5)
            self.safety = tk.StringVar(value="Yes" if self.row.safety else "No")
            ttk.Combobox(master, textvariable=self.safety, values=["Yes", "No"], state="readonly").grid(row=6, column=1, padx=5, pady=5)

            ttk.Label(master, text="Rationale").grid(row=7, column=0, sticky="ne", padx=5, pady=5)
            self.rat = tk.Text(master, width=30, height=3)
            self.rat.insert("1.0", self.row.rationale)
            self.rat.grid(row=7, column=1, padx=5, pady=5)

            ttk.Label(master, text="Covered").grid(row=8, column=0, sticky="e", padx=5, pady=5)
            self.cov = tk.StringVar(value="Yes" if self.row.covered else "No")
            ttk.Combobox(master, textvariable=self.cov, values=["Yes", "No"], state="readonly").grid(row=8, column=1, padx=5, pady=5)

            ttk.Label(master, text="Covered By").grid(row=9, column=0, sticky="e", padx=5, pady=5)
            malfs = [e.malfunction for e in self.app.hazop_entries]
            self.cov_by = tk.StringVar(value=self.row.covered_by)
            ttk.Combobox(master, textvariable=self.cov_by, values=malfs, state="readonly").grid(row=9, column=1, padx=5, pady=5)

        def apply(self):
            self.row.function = self.func.get()
            self.row.malfunction = self.mal.get()
            self.row.mtype = self.typ.get()
            self.row.scenario = self.scen.get()
            self.row.conditions = self.cond.get()
            self.row.hazard = self.haz.get("1.0", "end-1c")
            self.row.safety = self.safety.get() == "Yes"
            self.row.rationale = self.rat.get("1.0", "end-1c")
            self.row.covered = self.cov.get() == "Yes"
            self.row.covered_by = self.cov_by.get()

    def add_row(self):
        dlg = self.RowDialog(self)
        if dlg.row.function:
            self.app.hazop_entries.append(dlg.row)
            self.refresh()

    def edit_row(self):
        sel = self.tree.focus()
        if not sel:
            return
        idx = self.tree.index(sel)
        row = self.app.hazop_entries[idx]
        dlg = self.RowDialog(self, row)
        self.refresh()

    def del_row(self):
        sel = self.tree.selection()
        for iid in sel:
            idx = self.tree.index(iid)
            if idx < len(self.app.hazop_entries):
                del self.app.hazop_entries[idx]
        self.refresh()

    def load_analysis(self):
        if not self.app.reliability_analyses:
            messagebox.showwarning("Load", "No saved analyses")
            return
        win = tk.Toplevel(self)
        win.title("Select Analysis")
        lb = tk.Listbox(win, height=8, width=40)
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        for ra in self.app.reliability_analyses:
            lb.insert(tk.END, ra.name)
        def do_load():
            sel = lb.curselection()
            if not sel:
                return
            ra = self.app.reliability_analyses[sel[0]]
            self.standard_var.set(ra.standard)
            self.profile_var.set(ra.profile)
            self.components = copy.deepcopy(ra.components)
            self.app.reliability_total_fit = ra.total_fit
            self.app.spfm = ra.spfm
            self.app.lpfm = ra.lpfm
            self.app.reliability_dc = ra.dc
            win.destroy()
            self.refresh_tree()
            self.formula_label.config(
                text=f"Total FIT: {ra.total_fit:.2f}  DC: {ra.dc:.2f}  SPFM: {ra.spfm:.2f}  LPFM: {ra.lpfm:.2f}"
            )
        ttk.Button(win, text="Load", command=do_load).pack(side=tk.RIGHT, padx=5, pady=5)

    def save_analysis(self):
        if not self.components:
            messagebox.showwarning("Save", "No components defined")
            return
        name = simpledialog.askstring("Save Analysis", "Enter analysis name:")
        if not name:
            return
        ra = ReliabilityAnalysis(
            name,
            self.standard_var.get(),
            self.profile_var.get(),
            copy.deepcopy(self.components),
            self.app.reliability_total_fit,
            self.app.spfm,
            self.app.lpfm,
            self.app.reliability_dc,
        )
        self.app.reliability_analyses.append(ra)
        messagebox.showinfo("Save", "Analysis saved")


class HaraWindow(tk.Toplevel):
    COLS = [
        "malfunction","severity","sev_rationale","controllability",
        "cont_rationale","exposure","exp_rationale","asil","safety_goal"
    ]

    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title("HARA Analysis")
        self.tree = ttk.Treeview(self, columns=self.COLS, show="headings")
        for c in self.COLS:
            self.tree.heading(c, text=c.replace("_"," ").title())
            self.tree.column(c, width=120)
        self.tree.pack(fill=tk.BOTH, expand=True)
        btn = ttk.Frame(self)
        btn.pack()
        ttk.Button(btn, text="Add", command=self.add_row).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(btn, text="Edit", command=self.edit_row).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(btn, text="Delete", command=self.del_row).pack(side=tk.LEFT, padx=2, pady=2)
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for row in self.app.hara_entries:
            vals = [
                row.malfunction, row.severity, row.sev_rationale,
                row.controllability, row.cont_rationale,
                row.exposure, row.exp_rationale,
                row.asil, row.safety_goal
            ]
            self.tree.insert("", "end", values=vals)
        self.app.sync_hara_to_safety_goals()

    class RowDialog(simpledialog.Dialog):
        def __init__(self, parent, app, row=None):
            self.app = app
            self.row = row or HaraEntry("",1,"",1,"",1,"","QM","")
            super().__init__(parent, title="Edit HARA Row")

        def body(self, master):
            malfs = [e.malfunction for e in self.app.hazop_entries if e.safety]
            goals = [te.safety_goal_description or (te.user_name or f"SG {te.unique_id}") for te in self.app.top_events]
            ttk.Label(master, text="Malfunction").grid(row=0,column=0,sticky="e")
            self.mal_var = tk.StringVar(value=self.row.malfunction)
            ttk.Combobox(master, textvariable=self.mal_var, values=malfs, state="readonly").grid(row=0,column=1)
            ttk.Label(master, text="Severity").grid(row=1,column=0,sticky="e")
            self.sev_var = tk.StringVar(value=str(self.row.severity))
            sev_cb = ttk.Combobox(master, textvariable=self.sev_var, values=["1","2","3"], state="readonly")
            sev_cb.grid(row=1,column=1)
            ttk.Label(master, text="Severity Rationale").grid(row=2,column=0,sticky="e")
            self.sev_rat = tk.Entry(master)
            self.sev_rat.insert(0, self.row.sev_rationale)
            self.sev_rat.grid(row=2,column=1)
            ttk.Label(master, text="Controllability").grid(row=3,column=0,sticky="e")
            self.cont_var = tk.StringVar(value=str(self.row.controllability))
            cont_cb = ttk.Combobox(master, textvariable=self.cont_var, values=["1","2","3"], state="readonly")
            cont_cb.grid(row=3,column=1)
            ttk.Label(master, text="Controllability Rationale").grid(row=4,column=0,sticky="e")
            self.cont_rat = tk.Entry(master)
            self.cont_rat.insert(0, self.row.cont_rationale)
            self.cont_rat.grid(row=4,column=1)
            ttk.Label(master, text="Exposure").grid(row=5,column=0,sticky="e")
            self.exp_var = tk.StringVar(value=str(self.row.exposure))
            exp_cb = ttk.Combobox(master, textvariable=self.exp_var, values=["1","2","3","4"], state="readonly")
            exp_cb.grid(row=5,column=1)
            ttk.Label(master, text="Exposure Rationale").grid(row=6,column=0,sticky="e")
            self.exp_rat = tk.Entry(master)
            self.exp_rat.insert(0, self.row.exp_rationale)
            self.exp_rat.grid(row=6,column=1)
            ttk.Label(master, text="ASIL").grid(row=7,column=0,sticky="e")
            self.asil_var = tk.StringVar(value=self.row.asil)
            asil_lbl = ttk.Label(master, textvariable=self.asil_var)
            asil_lbl.grid(row=7,column=1)
            ttk.Label(master, text="Safety Goal").grid(row=8,column=0,sticky="e")
            self.sg_var = tk.StringVar(value=self.row.safety_goal)
            ttk.Combobox(master, textvariable=self.sg_var, values=goals, state="readonly").grid(row=8,column=1)

            def recalc(_=None):
                try:
                    s = int(self.sev_var.get())
                    c = int(self.cont_var.get())
                    e = int(self.exp_var.get())
                except ValueError:
                    self.asil_var.set("QM")
                    return
                self.asil_var.set(calc_asil(s,c,e))

            sev_cb.bind("<<ComboboxSelected>>", recalc)
            cont_cb.bind("<<ComboboxSelected>>", recalc)
            exp_cb.bind("<<ComboboxSelected>>", recalc)
            recalc()

        def apply(self):
            self.row.malfunction = self.mal_var.get()
            self.row.severity = int(self.sev_var.get())
            self.row.sev_rationale = self.sev_rat.get()
            self.row.controllability = int(self.cont_var.get())
            self.row.cont_rationale = self.cont_rat.get()
            self.row.exposure = int(self.exp_var.get())
            self.row.exp_rationale = self.exp_rat.get()
            self.row.asil = self.asil_var.get()
            self.row.safety_goal = self.sg_var.get()

    def add_row(self):
        dlg = self.RowDialog(self, self.app)
        self.app.hara_entries.append(dlg.row)
        self.refresh()

    def edit_row(self):
        sel = self.tree.focus()
        if not sel:
            return
        idx = self.tree.index(sel)
        dlg = self.RowDialog(self, self.app, self.app.hara_entries[idx])
        self.refresh()

    def del_row(self):
        sel = self.tree.selection()
        for iid in sel:
            idx = self.tree.index(iid)
            if idx < len(self.app.hara_entries):
                del self.app.hara_entries[idx]
        self.refresh()




    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title("FI2TC Analysis")
        cols = ("fi","tc","scenario","hazard","mitigation","asil")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
            self.tree.column(c, width=100)
        self.tree.pack(fill=tk.BOTH, expand=True)
        btn = ttk.Frame(self)
        btn.pack()
        ttk.Button(btn, text="Add", command=self.add_row).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(btn, text="Edit", command=self.edit_row).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(btn, text="Delete", command=self.del_row).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(btn, text="Export CSV", command=self.export_csv).pack(side=tk.LEFT, padx=2, pady=2)
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for row in self.app.fi2tc_entries:
            self.tree.insert("", "end", values=(row.get("fi"), row.get("tc"), row.get("scenario"), row.get("hazard"), row.get("mitigation"), row.get("asil")))

    class RowDialog(simpledialog.Dialog):
        def __init__(self, parent, app, data=None):
            self.app = app
            self.data = data or {"fi":"","tc":"","scenario":"","hazard":"","mitigation":"","asil":""}
            super().__init__(parent, title="Edit Row")
        def body(self, master):
            fi_names = [n.user_name or f"FI {n.unique_id}" for n in self.app.get_all_functional_insufficiencies()]
            tc_names = [n.user_name or f"TC {n.unique_id}" for n in self.app.get_all_triggering_conditions()]
            self.fi_var = tk.StringVar(value=self.data.get("fi"))
            ttk.Combobox(master, textvariable=self.fi_var, values=fi_names, state="readonly").grid(row=0,column=1)
            ttk.Label(master, text="Functional Insufficiency").grid(row=0,column=0,sticky="e")
            self.tc_var = tk.StringVar(value=self.data.get("tc"))
            ttk.Combobox(master, textvariable=self.tc_var, values=tc_names, state="readonly").grid(row=1,column=1)
            ttk.Label(master, text="Triggering Condition").grid(row=1,column=0,sticky="e")
            ttk.Label(master, text="Scenario").grid(row=2,column=0,sticky="e")
            self.sc_var = tk.Entry(master)
            self.sc_var.insert(0, self.data.get("scenario"))
            self.sc_var.grid(row=2,column=1)
            ttk.Label(master, text="Hazard").grid(row=3,column=0,sticky="e")
            self.haz_var = tk.Entry(master)
            self.haz_var.insert(0, self.data.get("hazard"))
            self.haz_var.grid(row=3,column=1)
            ttk.Label(master, text="Mitigation").grid(row=4,column=0,sticky="e")
            self.mit_var = tk.Entry(master)
            self.mit_var.insert(0, self.data.get("mitigation"))
            self.mit_var.grid(row=4,column=1)
            ttk.Label(master, text="ASIL").grid(row=5,column=0,sticky="e")
            self.asil_var = tk.Entry(master)
            self.asil_var.insert(0, self.data.get("asil"))
            self.asil_var.grid(row=5,column=1)
        def apply(self):
            self.data["fi"] = self.fi_var.get()
            self.data["tc"] = self.tc_var.get()
            self.data["scenario"] = self.sc_var.get()
            self.data["hazard"] = self.haz_var.get()
            self.data["mitigation"] = self.mit_var.get()
            self.data["asil"] = self.asil_var.get()

    def add_row(self):
        dlg = self.RowDialog(self, self.app)
        self.app.fi2tc_entries.append(dlg.data)
        self.refresh()
    def edit_row(self):
        sel = self.tree.focus()
        if not sel: return
        idx = self.tree.index(sel)
        data = self.app.fi2tc_entries[idx]
        dlg = self.RowDialog(self, self.app, data)
        self.refresh()
    def del_row(self):
        sel = self.tree.selection()
        for iid in sel:
            idx = self.tree.index(iid)
            if idx < len(self.app.fi2tc_entries):
                del self.app.fi2tc_entries[idx]
        self.refresh()
    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")])
        if not path: return
        with open(path,"w",newline="") as f:
            w=csv.writer(f)
            w.writerow(["Functional Insufficiency","Triggering Condition","Scenario","Hazard","Mitigation","ASIL"])
            for r in self.app.fi2tc_entries:
                w.writerow([r.get("fi"),r.get("tc"),r.get("scenario"),r.get("hazard"),r.get("mitigation"),r.get("asil")])
        messagebox.showinfo("Export","FI2TC exported")

class TC2FIWindow(tk.Toplevel):
    COLS = [
        "id",
        "known_use_case",
        "occurrence",
        "impacted_function",
        "arch_elements",
        "interfaces",
        "functional_insufficiency",
        "vehicle_effect",
        "severity",
        "design_measures",
        "verification",
        "measure_effectiveness",
        "scene",
        "scenario",
        "driver_behavior",
        "triggering_condition",
        "tc_effect",
        "mitigation",
        "acceptance",
    ]

    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title("TC2FI Analysis")
        self.tree = ttk.Treeview(self, columns=self.COLS, show="headings")
        for c in self.COLS:
            self.tree.heading(c, text=c.replace("_", " ").title())
            self.tree.column(c, width=120)
        self.tree.pack(fill=tk.BOTH, expand=True)

        btn = ttk.Frame(self)
        btn.pack()
        ttk.Button(btn, text="Add", command=self.add_row).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(btn, text="Edit", command=self.edit_row).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(btn, text="Delete", command=self.del_row).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(btn, text="Export CSV", command=self.export_csv).pack(side=tk.LEFT, padx=2, pady=2)
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for row in self.app.tc2fi_entries:
            self.tree.insert("", "end", values=[row.get(k, "") for k in self.COLS])

    class RowDialog(simpledialog.Dialog):
        def __init__(self, parent, app, data=None):
            self.app = app
            default = {k: "" for k in TC2FIWindow.COLS}
            self.data = data or default
            super().__init__(parent, title="Edit Row")

        def body(self, master):
            tc_names = [n.user_name or f"TC {n.unique_id}" for n in self.app.get_all_triggering_conditions()]
            fi_names = [n.user_name or f"FI {n.unique_id}" for n in self.app.get_all_functional_insufficiencies()]
            func_names = self.app.get_all_function_names()
            comp_names = self.app.get_all_component_names()
            scen_names = self.app.get_all_scenario_names()
            scene_names = self.app.get_all_scenery_names()
            self.widgets = {}
            r = 0

            def refresh_funcs(*_):
                comp = self.widgets.get("arch_elements")
                if isinstance(comp, tk.StringVar):
                    opts = sorted({e.function for e in self.app.hazop_entries if not comp.get() or e.component == comp.get()})
                else:
                    opts = func_names
                if "impacted_function" in self.widgets:
                    w = self.widgets["impacted_function_widget"]
                    w["values"] = opts

            for col in TC2FIWindow.COLS:
                ttk.Label(master, text=col.replace("_", " ").title()).grid(row=r, column=0, sticky="e")
                if col == "functional_insufficiency":
                    var = tk.StringVar(value=self.data.get(col, ""))
                    cb = ttk.Combobox(master, textvariable=var, values=fi_names, state="readonly")
                    cb.grid(row=r, column=1)
                    self.widgets[col] = var
                elif col == "triggering_condition":
                    var = tk.StringVar(value=self.data.get(col, ""))
                    cb = ttk.Combobox(master, textvariable=var, values=tc_names, state="readonly")
                    cb.grid(row=r, column=1)
                    self.widgets[col] = var
                elif col == "impacted_function":
                    var = tk.StringVar(value=self.data.get(col, ""))
                    cb = ttk.Combobox(master, textvariable=var, values=func_names, state="readonly")
                    cb.grid(row=r, column=1)
                    self.widgets[col] = var
                    self.widgets["impacted_function_widget"] = cb
                elif col == "arch_elements":
                    var = tk.StringVar(value=self.data.get(col, ""))
                    cb = ttk.Combobox(master, textvariable=var, values=comp_names, state="readonly")
                    cb.grid(row=r, column=1)
                    cb.bind("<<ComboboxSelected>>", refresh_funcs)
                    self.widgets[col] = var
                elif col == "scene":
                    var = tk.StringVar(value=self.data.get(col, ""))
                    cb = ttk.Combobox(master, textvariable=var, values=scene_names, state="readonly")
                    cb.grid(row=r, column=1)
                    self.widgets[col] = var
                elif col == "scenario":
                    var = tk.StringVar(value=self.data.get(col, ""))
                    cb = ttk.Combobox(master, textvariable=var, values=scen_names, state="readonly")
                    cb.grid(row=r, column=1)
                    self.widgets[col] = var
                elif col == "severity":
                    var = tk.StringVar(value=self.data.get(col, ""))
                    cb = ttk.Combobox(master, textvariable=var, values=["1", "2", "3"], state="readonly")
                    cb.grid(row=r, column=1)
                    self.widgets[col] = var
                else:
                    ent = tk.Entry(master)
                    ent.insert(0, self.data.get(col, ""))
                    ent.grid(row=r, column=1)
                    self.widgets[col] = ent
                r += 1
            refresh_funcs()

        def apply(self):
            for col, widget in self.widgets.items():
                if isinstance(widget, tk.Entry):
                    self.data[col] = widget.get()
                else:
                    self.data[col] = widget.get()

    def add_row(self):
        dlg = self.RowDialog(self, self.app)
        self.app.tc2fi_entries.append(dlg.data)
        self.refresh()

    def edit_row(self):
        sel = self.tree.focus()
        if not sel:
            return
        idx = self.tree.index(sel)
        data = self.app.tc2fi_entries[idx]
        dlg = self.RowDialog(self, self.app, data)
        self.refresh()

    def del_row(self):
        sel = self.tree.selection()
        for iid in sel:
            idx = self.tree.index(iid)
            if idx < len(self.app.tc2fi_entries):
                del self.app.tc2fi_entries[idx]
        self.refresh()

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(self.COLS)
            for r in self.app.tc2fi_entries:
                w.writerow([r.get(k, "") for k in self.COLS])
        messagebox.showinfo("Export", "TC2FI exported")



