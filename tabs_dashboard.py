"""
tabs_dashboard.py - Overview screen: pick a month, see totals and who
still owes rent.
"""

import tkinter as tk
from tkinter import ttk
import datetime

import widgets as w


class DashboardTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.db = app.db
        self.period = w.current_period()

        self._build()
        self.refresh()

    def _build(self):
        # ---- header / month picker (wraps onto a new row on narrow screens)
        header = w.FlowFrame(self)
        header.pack(fill="x", padx=16, pady=(16, 8))

        header.add(ttk.Button(header, text="◀", width=3, command=self.prev_month))
        self.month_label = ttk.Label(header, text="", font=("Segoe UI", 14, "bold"))
        header.add(self.month_label, pad_left=10)
        header.add(ttk.Button(header, text="▶", width=3, command=self.next_month), pad_left=10)
        header.add(ttk.Button(header, text="Today", command=self.go_today), pad_left=10)

        header.add(ttk.Button(header, text="Generate rent records for this month",
                               command=self.generate_month), pad_left=16)

        # ---- stat cards
        self.cards_frame = ttk.Frame(self)
        self.cards_frame.pack(fill="x", padx=16, pady=8)
        for i in range(5):
            self.cards_frame.columnconfigure(i, weight=1)

        self.card_due = w.stat_card(self.cards_frame, "Total Due", "0", w.COLOR_TEXT)
        self.card_paid = w.stat_card(self.cards_frame, "Collected", "0", w.COLOR_SUCCESS)
        self.card_pending = w.stat_card(self.cards_frame, "Pending", "0", w.COLOR_WARNING)
        self.card_overdue = w.stat_card(self.cards_frame, "Overdue Tenants", "0", w.COLOR_DANGER)
        self.card_occupancy = w.stat_card(self.cards_frame, "Occupancy", "0 / 0", w.COLOR_PRIMARY)

        for i, c in enumerate([self.card_due, self.card_paid, self.card_pending,
                                self.card_overdue, self.card_occupancy]):
            c.grid(row=0, column=i, sticky="nsew", padx=6)

        # ---- overdue / unpaid list
        list_frame = ttk.LabelFrame(self, text="Needs attention this month")
        list_frame.pack(fill="both", expand=True, padx=16, pady=(8, 16))

        columns = ("tenant", "property_unit", "due", "paid", "balance", "status", "due_date")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        headings = {
            "tenant": "Tenant", "property_unit": "Property / Unit", "due": "Amount Due",
            "paid": "Amount Paid", "balance": "Balance", "status": "Status",
            "due_date": "Due Date",
        }
        widths = {"tenant": 160, "property_unit": 180, "due": 100, "paid": 100,
                  "balance": 100, "status": 90, "due_date": 100}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")
        self.tree.pack(fill="both", expand=True, side="left")

        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)

        for status, color in w.STATUS_COLORS.items():
            self.tree.tag_configure(status, background=color)

        self.tree.bind("<Double-1>", self.go_to_rent_tab)

    # ------------------------------------------------------------ logic
    def refresh(self):
        self.month_label.config(text=w.month_name(self.period))
        summary = self.db.month_summary(self.period)

        self._set_card(self.card_due, w.fmt_money(summary["total_due"]))
        self._set_card(self.card_paid, w.fmt_money(summary["total_paid"]))
        self._set_card(self.card_pending, w.fmt_money(summary["total_pending"]))
        # Overdue Tenants must reflect overdue balances across ALL months,
        # not just whichever month is currently selected here - otherwise
        # a tenant overdue on a past month never shows up while you're
        # looking at the current month.
        self._set_card(self.card_overdue, str(self.db.overdue_tenant_count()))

        total_units, occupied = self.db.occupancy_summary()
        self._set_card(self.card_occupancy, f"{occupied} / {total_units}")

        for row in self.tree.get_children():
            self.tree.delete(row)

        needs_attention = [
            r for r in summary["records"] if r["amount_paid"] < r["amount_due"]
        ]
        if not needs_attention and not summary["records"]:
            self.tree.insert("", "end", values=(
                "No rent records yet for this month.", "", "", "", "", "", ""
            ))
            return
        for r in needs_attention:
            status = w.compute_status(r["amount_due"], r["amount_paid"], r["due_date"])
            balance = r["amount_due"] - r["amount_paid"]
            self.tree.insert("", "end", iid=str(r["id"]), values=(
                r["tenant_name"],
                f"{r['property_name'] or ''} / {r['unit_number'] or ''}",
                w.fmt_money(r["amount_due"]),
                w.fmt_money(r["amount_paid"]),
                w.fmt_money(balance),
                status,
                r["due_date"] or "",
            ), tags=(status,))

    def _set_card(self, card_frame, value):
        # value label is the second child packed into the card
        labels = [c for c in card_frame.winfo_children() if isinstance(c, tk.Label)]
        if len(labels) >= 2:
            labels[1].config(text=value)

    def prev_month(self):
        self.period = w.shift_period(self.period, -1)
        self.refresh()

    def next_month(self):
        self.period = w.shift_period(self.period, 1)
        self.refresh()

    def go_today(self):
        self.period = w.current_period()
        self.refresh()

    def generate_month(self):
        created = self.db.generate_for_month(self.period)
        self.refresh()
        self.app.rent_tab.refresh()
        from tkinter import messagebox
        messagebox.showinfo(
            "Rent records generated",
            f"{created} new rent record(s) created for {w.month_name(self.period)}."
            if created else
            f"All active tenants already have rent records for {w.month_name(self.period)}."
        )

    def go_to_rent_tab(self, event):
        self.app.rent_tab.period = self.period
        self.app.notebook.select(self.app.rent_tab.notebook_page)
        self.app.rent_tab.refresh()
