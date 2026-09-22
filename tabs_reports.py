"""
tabs_reports.py - yearly collection-rate report, net income view, and
CSV exports for accountants / spreadsheets.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
import csv

import widgets as w


class ReportsTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.db = app.db
        self.year_var = tk.StringVar(value=str(datetime.date.today().year))
        self._build()
        self.refresh()

    def _build(self):
        top = w.FlowFrame(self)
        top.pack(fill="x", padx=16, pady=(16, 8))

        top.add(ttk.Label(top, text="Year:"))
        top.add(ttk.Spinbox(top, from_=2000, to=2100, textvariable=self.year_var, width=8,
                             command=self.refresh), pad_left=4)
        top.add(ttk.Button(top, text="Refresh", command=self.refresh), pad_left=16)

        top.add(ttk.Button(top, text="Export Rent Records (CSV)",
                            command=self.export_rent_csv), pad_left=16)
        top.add(ttk.Button(top, text="Export Payments (CSV)",
                            command=self.export_payments_csv), pad_left=4)
        top.add(ttk.Button(top, text="Export Tenants (CSV)",
                            command=self.export_tenants_csv), pad_left=4)
        top.add(ttk.Button(top, text="Export By-Tenant Year Summary (CSV)",
                            command=self.export_tenant_year_csv), pad_left=4)

        # ---- yearly tables (by month / by tenant)
        self.sub_notebook = ttk.Notebook(self)
        self.sub_notebook.pack(fill="both", expand=True, padx=16, pady=8)

        month_frame = ttk.Frame(self.sub_notebook)
        tenant_frame = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(month_frame, text="  By Month  ")
        self.sub_notebook.add(tenant_frame, text="  By Tenant  ")

        columns = ("month", "due", "paid", "pending", "rate")
        tree_holder, self.tree = w.scrolled_tree(month_frame, columns, height=13)
        headings = {"month": "Month", "due": "Total Due", "paid": "Collected",
                    "pending": "Pending", "rate": "Collection Rate"}
        widths = {"month": 130, "due": 120, "paid": 120, "pending": 120, "rate": 130}
        for c in columns:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c], anchor="w")
        tree_holder.pack(fill="both", expand=True, padx=8, pady=8)

        tcolumns = ("tenant", "property_unit", "due", "paid", "balance", "rate", "status")
        tenant_tree_holder, self.tenant_tree = w.scrolled_tree(tenant_frame, tcolumns, height=13)
        theadings = {"tenant": "Tenant", "property_unit": "Property / Unit",
                     "due": "Total Due (Year)", "paid": "Total Paid (Year)",
                     "balance": "Balance", "rate": "Collection Rate", "status": "Status"}
        twidths = {"tenant": 160, "property_unit": 170, "due": 120, "paid": 120,
                   "balance": 100, "rate": 110, "status": 90}
        for c in tcolumns:
            self.tenant_tree.heading(c, text=theadings[c])
            self.tenant_tree.column(c, width=twidths[c], anchor="w")
        tenant_tree_holder.pack(fill="both", expand=True, padx=8, pady=8)
        self.tenant_tree.tag_configure("inactive", foreground=w.COLOR_MUTED)

        # ---- bottom summary cards
        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=16, pady=(0, 16))
        for i in range(4):
            bottom.columnconfigure(i, weight=1)
        self.card_due = w.stat_card(bottom, "Year Total Due", "0")
        self.card_paid = w.stat_card(bottom, "Year Total Collected", "0", w.COLOR_SUCCESS)
        self.card_expenses = w.stat_card(bottom, "Year Total Expenses", "0", w.COLOR_DANGER)
        self.card_net = w.stat_card(bottom, "Net Income (collected - expenses)", "0", w.COLOR_PRIMARY)
        for i, c in enumerate([self.card_due, self.card_paid, self.card_expenses, self.card_net]):
            c.grid(row=0, column=i, sticky="nsew", padx=6)

    # ------------------------------------------------------------ data
    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in self.tenant_tree.get_children():
            self.tenant_tree.delete(row)
        try:
            year = int(self.year_var.get())
        except ValueError:
            return
        rows = self.db.year_collection_summary(year)
        year_due = year_paid = 0
        for r in rows:
            due = r["due"] or 0
            paid = r["paid"] or 0
            year_due += due
            year_paid += paid
            rate = f"{(paid / due * 100):.1f}%" if due else "—"
            self.tree.insert("", "end", values=(
                w.month_name(r["period"]), w.fmt_money(due), w.fmt_money(paid),
                w.fmt_money(due - paid), rate,
            ))

        tenant_rows = self.db.tenant_year_summary(year)
        for t in tenant_rows:
            due = t["due"] or 0
            paid = t["paid"] or 0
            balance = due - paid
            rate = f"{(paid / due * 100):.1f}%" if due else "—"
            tag = "inactive" if not t["is_active"] else ""
            self.tenant_tree.insert("", "end", values=(
                t["tenant_name"],
                f"{t['property_name'] or ''} / {t['unit_number'] or ''}".strip(" /"),
                w.fmt_money(due),
                w.fmt_money(paid),
                w.fmt_money(balance),
                rate,
                "Active" if t["is_active"] else "Moved out",
            ), tags=(tag,))

        expenses = self.db.list_expenses()
        year_expenses = sum(
            e["amount"] for e in expenses if e["expense_date"] and e["expense_date"].startswith(str(year))
        )

        self._set_card(self.card_due, w.fmt_money(year_due))
        self._set_card(self.card_paid, w.fmt_money(year_paid))
        self._set_card(self.card_expenses, w.fmt_money(year_expenses))
        self._set_card(self.card_net, w.fmt_money(year_paid - year_expenses))

    def _set_card(self, card_frame, value):
        labels = [c for c in card_frame.winfo_children() if isinstance(c, tk.Label)]
        if len(labels) >= 2:
            labels[1].config(text=value)

    # ------------------------------------------------------------ exports
    def export_rent_csv(self):
        path = filedialog.asksaveasfilename(
            title="Export rent records", defaultextension=".csv",
            initialfile="rent_records.csv", filetypes=[("CSV", "*.csv")],
        )
        if not path:
            return
        rows = self.db.list_rent_records()
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Period", "Tenant", "Property", "Unit", "Amount Due",
                              "Amount Paid", "Balance", "Status", "Due Date"])
            for r in rows:
                status = w.compute_status(r["amount_due"], r["amount_paid"], r["due_date"])
                writer.writerow([
                    r["period"], r["tenant_name"], r["property_name"] or "", r["unit_number"] or "",
                    r["amount_due"], r["amount_paid"], r["amount_due"] - r["amount_paid"],
                    status, r["due_date"] or "",
                ])
        messagebox.showinfo("Export complete", f"Saved to:\n{path}")

    def export_payments_csv(self):
        path = filedialog.asksaveasfilename(
            title="Export payments", defaultextension=".csv",
            initialfile="payments.csv", filetypes=[("CSV", "*.csv")],
        )
        if not path:
            return
        records = self.db.list_rent_records()
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Period", "Tenant", "Payment Date", "Amount", "Method", "Notes"])
            for r in records:
                for p in self.db.list_payments_for_record(r["id"]):
                    writer.writerow([r["period"], r["tenant_name"], p["payment_date"],
                                      p["amount"], p["method"] or "", p["notes"] or ""])
        messagebox.showinfo("Export complete", f"Saved to:\n{path}")

    def export_tenants_csv(self):
        path = filedialog.asksaveasfilename(
            title="Export tenants", defaultextension=".csv",
            initialfile="tenants.csv", filetypes=[("CSV", "*.csv")],
        )
        if not path:
            return
        rows = self.db.list_tenants()
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Property", "Unit", "Phone", "Email", "Lease Start",
                              "Lease End", "Monthly Rent", "Deposit", "Active", "Notes"])
            for t in rows:
                writer.writerow([
                    t["name"], t["property_name"] or "", t["unit_number"] or "", t["phone"] or "",
                    t["email"] or "", t["lease_start"] or "", t["lease_end"] or "",
                    t["monthly_rent"], t["deposit"], "Yes" if t["is_active"] else "No", t["notes"] or "",
                ])
        messagebox.showinfo("Export complete", f"Saved to:\n{path}")

    def export_tenant_year_csv(self):
        try:
            year = int(self.year_var.get())
        except ValueError:
            messagebox.showwarning("Invalid year", "Enter a valid year first.")
            return
        path = filedialog.asksaveasfilename(
            title="Export by-tenant year summary", defaultextension=".csv",
            initialfile=f"tenant_year_summary_{year}.csv", filetypes=[("CSV", "*.csv")],
        )
        if not path:
            return
        rows = self.db.tenant_year_summary(year)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Year", "Tenant", "Property", "Unit", "Total Due",
                              "Total Paid", "Balance", "Collection Rate", "Status"])
            for t in rows:
                due = t["due"] or 0
                paid = t["paid"] or 0
                rate = f"{(paid / due * 100):.1f}%" if due else ""
                writer.writerow([
                    year, t["tenant_name"], t["property_name"] or "", t["unit_number"] or "",
                    due, paid, due - paid, rate, "Active" if t["is_active"] else "Moved out",
                ])
        messagebox.showinfo("Export complete", f"Saved to:\n{path}")
