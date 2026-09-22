"""
tabs_expenses.py - optional property expense tracking (repairs, taxes,
maintenance) so Reports can show net income, not just rent collected.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime

import widgets as w


class ExpenseDialog(tk.Toplevel):
    def __init__(self, parent, properties):
        super().__init__(parent)
        self.configure(bg=w.COLOR_BG)
        self.title("Add Expense")
        self.resizable(False, False)
        self.result = None
        self.grab_set()

        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Property", foreground=w.COLOR_MUTED).pack(anchor="w")
        self.prop_map = {"— General / Not property-specific —": None}
        for p in properties:
            self.prop_map[p["name"]] = p["id"]
        self.prop_var = tk.StringVar(value="— General / Not property-specific —")
        ttk.Combobox(frm, textvariable=self.prop_var, width=28, state="readonly",
                     values=list(self.prop_map.keys())).pack(fill="x", pady=4)

        ttk.Label(frm, text="Category", foreground=w.COLOR_MUTED).pack(anchor="w", pady=(4, 0))
        self.cat_var = tk.StringVar(value="Maintenance")
        ttk.Combobox(frm, textvariable=self.cat_var, width=28, values=[
            "Maintenance", "Repairs", "Property Tax", "Insurance", "Utilities",
            "Cleaning", "Legal/Admin", "Other",
        ]).pack(fill="x", pady=4)

        self.amount_e = w.LabeledEntry(frm, "Amount *", width=28)
        self.amount_e.pack(fill="x", pady=4)

        self.date_e = w.LabeledEntry(frm, "Date (YYYY-MM-DD) *", width=28)
        self.date_e.set(datetime.date.today().isoformat())
        self.date_e.pack(fill="x", pady=4)

        ttk.Label(frm, text="Notes", foreground=w.COLOR_MUTED).pack(anchor="w", pady=(4, 0))
        self.notes_txt = tk.Text(frm, width=28, height=3, **w.entry_colors())
        self.notes_txt.pack(fill="x", pady=4)

        btns = ttk.Frame(frm)
        btns.pack(fill="x", pady=(12, 0))
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(btns, text="Save", style="Accent.TButton", command=self.on_save).pack(side="right")

        self.amount_e.entry.focus_set()

    def on_save(self):
        try:
            amount = float(self.amount_e.get())
        except ValueError:
            messagebox.showwarning("Invalid amount", "Enter a valid number.")
            return
        try:
            datetime.datetime.strptime(self.date_e.get(), "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Invalid date", "Date must be in YYYY-MM-DD format.")
            return
        self.result = {
            "property_id": self.prop_map.get(self.prop_var.get()),
            "category": self.cat_var.get(),
            "amount": amount,
            "expense_date": self.date_e.get().strip(),
            "notes": self.notes_txt.get("1.0", "end").strip(),
        }
        self.destroy()


class ExpensesTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.db = app.db
        self._build()
        self.refresh()

    def _build(self):
        top = w.FlowFrame(self)
        top.pack(fill="x", padx=16, pady=(16, 8))
        top.add(ttk.Button(top, text="+ Add Expense", command=self.add_expense))
        top.add(ttk.Button(top, text="Delete Selected", command=self.delete_expense), pad_left=6)
        self.total_label = ttk.Label(top, text="", foreground=w.COLOR_MUTED)
        top.add(self.total_label, pad_left=16)

        columns = ("date", "property", "category", "amount", "notes")
        tree_holder, self.tree = w.scrolled_tree(self, columns, height=20)
        headings = {"date": "Date", "property": "Property", "category": "Category",
                    "amount": "Amount", "notes": "Notes"}
        widths = {"date": 100, "property": 160, "category": 130, "amount": 100, "notes": 240}
        for c in columns:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c], anchor="w")
        tree_holder.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        rows = self.db.list_expenses()
        total = 0
        for e in rows:
            total += e["amount"]
            self.tree.insert("", "end", iid=str(e["id"]), values=(
                e["expense_date"], e["property_name"] or "General", e["category"] or "",
                w.fmt_money(e["amount"]), e["notes"] or "",
            ))
        self.total_label.config(text=f"Total expenses: {w.fmt_money(total)}")

    def add_expense(self):
        dlg = ExpenseDialog(self, self.db.list_properties())
        self.wait_window(dlg)
        if dlg.result:
            self.db.add_expense(**dlg.result)
            self.refresh()

    def delete_expense(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("No selection", "Select an expense first.")
            return
        if messagebox.askyesno("Delete expense", "Delete the selected expense?"):
            self.db.delete_expense(int(sel[0]))
            self.refresh()
