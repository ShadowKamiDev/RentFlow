"""
tabs_rent.py - the core rent tracking grid. Pick a month, see every
tenant's due/paid/balance/status, and record payments.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime

import widgets as w


class PaymentDialog(tk.Toplevel):
    def __init__(self, parent, tenant_name, balance, full_amount, edit_mode=False):
        super().__init__(parent)
        self.configure(bg=w.COLOR_BG)
        self.title("Edit payment" if edit_mode else f"Record payment — {tenant_name}")
        self.resizable(False, False)
        self.result = None
        self.grab_set()

        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)

        if not edit_mode:
            ttk.Label(frm, text=f"Remaining balance: {w.fmt_money(balance)}",
                      foreground=w.COLOR_MUTED).pack(anchor="w", pady=(0, 8))

        self.amount_e = w.LabeledEntry(frm, "Amount received *", width=26)
        self.amount_e.set(f"{full_amount:.2f}")
        self.amount_e.pack(fill="x", pady=4)

        self.date_e = w.LabeledEntry(frm, "Payment date (YYYY-MM-DD) *", width=26)
        self.date_e.set(datetime.date.today().isoformat())
        self.date_e.pack(fill="x", pady=4)

        ttk.Label(frm, text="Method", foreground=w.COLOR_MUTED).pack(anchor="w", pady=(4, 0))
        self.method_var = tk.StringVar(value="Bank Transfer")
        ttk.Combobox(frm, textvariable=self.method_var, width=24, values=[
            "Cash", "Bank Transfer", "UPI", "Cheque", "Card", "Other"
        ]).pack(fill="x", pady=4)

        ttk.Label(frm, text="Notes", foreground=w.COLOR_MUTED).pack(anchor="w", pady=(4, 0))
        self.notes_txt = tk.Text(frm, width=26, height=2, **w.entry_colors())
        self.notes_txt.pack(fill="x", pady=4)

        btns = ttk.Frame(frm)
        btns.pack(fill="x", pady=(12, 0))
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(btns, text="Save Payment", style="Accent.TButton",
                   command=self.on_save).pack(side="right")

        self.amount_e.entry.focus_set()
        self.amount_e.entry.selection_range(0, "end")

    def on_save(self):
        try:
            amount = float(self.amount_e.get())
        except ValueError:
            messagebox.showwarning("Invalid amount", "Enter a valid number.")
            return
        if amount <= 0:
            messagebox.showwarning("Invalid amount", "Amount must be greater than zero.")
            return
        try:
            datetime.datetime.strptime(self.date_e.get(), "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Invalid date", "Date must be in YYYY-MM-DD format.")
            return
        self.result = {
            "amount": amount,
            "payment_date": self.date_e.get().strip(),
            "method": self.method_var.get(),
            "notes": self.notes_txt.get("1.0", "end").strip(),
        }
        self.destroy()


class BulkPaidDialog(tk.Toplevel):
    """Mark a tenant paid for several months in one go, instead of one
    month at a time. Creates the rent record for each month if it
    doesn't exist yet (using the correct rent for that month) and logs
    a full payment against it."""

    def __init__(self, parent, tenant_name, default_period):
        super().__init__(parent)
        self.configure(bg=w.COLOR_BG)
        self.title(f"Mark paid — multiple months — {tenant_name}")
        self.resizable(False, False)
        self.result = None
        self.grab_set()

        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text=f"Tenant: {tenant_name}", font=("Segoe UI", 10, "bold")).pack(
            anchor="w", pady=(0, 8))

        self.start_e = w.LabeledEntry(frm, "Start month (YYYY-MM) *", width=26)
        self.start_e.set(default_period)
        self.start_e.pack(fill="x", pady=4)

        self.months_e = w.LabeledEntry(frm, "Number of months *", width=26)
        self.months_e.set("1")
        self.months_e.pack(fill="x", pady=4)

        self.date_e = w.LabeledEntry(frm, "Payment date (YYYY-MM-DD) *", width=26)
        self.date_e.set(datetime.date.today().isoformat())
        self.date_e.pack(fill="x", pady=4)

        ttk.Label(frm, text="Method", foreground=w.COLOR_MUTED).pack(anchor="w", pady=(4, 0))
        self.method_var = tk.StringVar(value="Bank Transfer")
        ttk.Combobox(frm, textvariable=self.method_var, width=24, values=[
            "Cash", "Bank Transfer", "UPI", "Cheque", "Card", "Other"
        ]).pack(fill="x", pady=4)

        ttk.Label(frm, text="Notes", foreground=w.COLOR_MUTED).pack(anchor="w", pady=(4, 0))
        self.notes_txt = tk.Text(frm, width=26, height=2, **w.entry_colors())
        self.notes_txt.pack(fill="x", pady=4)

        ttk.Label(frm, text="Existing months already fully paid are left\nalone; only unpaid/partial balances are charged.",
                  foreground=w.COLOR_MUTED, justify="left").pack(anchor="w", pady=(8, 0))

        btns = ttk.Frame(frm)
        btns.pack(fill="x", pady=(12, 0))
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(btns, text="Mark Paid", style="Accent.TButton",
                   command=self.on_save).pack(side="right")

        self.start_e.entry.focus_set()

    def on_save(self):
        start = self.start_e.get().strip()
        try:
            datetime.datetime.strptime(start, "%Y-%m")
        except ValueError:
            messagebox.showwarning("Invalid month", "Start month must be in YYYY-MM format.")
            return
        try:
            months = int(self.months_e.get())
            if months < 1:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid number", "Number of months must be a whole number, 1 or more.")
            return
        try:
            datetime.datetime.strptime(self.date_e.get(), "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Invalid date", "Payment date must be in YYYY-MM-DD format.")
            return
        self.result = {
            "start_period": start,
            "num_months": months,
            "payment_date": self.date_e.get().strip(),
            "method": self.method_var.get(),
            "notes": self.notes_txt.get("1.0", "end").strip(),
        }
        self.destroy()


class PaymentHistoryDialog(tk.Toplevel):
    """Shows every payment logged against a rent record, with Edit and
    Delete so a mistaken payment (e.g. an accidental 'Mark Fully Paid')
    can be corrected or undone instead of being stuck forever."""

    def __init__(self, parent, db, rent_record_id, on_change=None):
        super().__init__(parent)
        self.db = db
        self.rid = rent_record_id
        self.on_change = on_change
        self.configure(bg=w.COLOR_BG)
        self.title("Payment history")
        self.geometry("520x340")
        self.grab_set()

        columns = ("date", "amount", "method", "notes")
        tree_holder, self.tree = w.scrolled_tree(self, columns)
        for c, label, width in [("date", "Date", 100), ("amount", "Amount", 100),
                                 ("method", "Method", 110), ("notes", "Notes", 150)]:
            self.tree.heading(c, text=label)
            self.tree.column(c, width=width)
        tree_holder.pack(fill="both", expand=True, padx=8, pady=8)

        self.empty_label = ttk.Label(self, text="No payments recorded yet for this month.")

        btns = ttk.Frame(self, padding=(8, 0, 8, 8))
        btns.pack(fill="x")
        ttk.Button(btns, text="Edit Selected", command=self.edit_selected).pack(side="left")
        ttk.Button(btns, text="Delete Selected (undo)", command=self.delete_selected).pack(
            side="left", padx=6)
        ttk.Button(btns, text="Close", command=self.destroy).pack(side="right")

        self._reload()

    def _reload(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        payments = self.db.list_payments_for_record(self.rid)
        self.empty_label.pack_forget()
        if not payments:
            self.empty_label.pack(pady=8)
        for p in payments:
            self.tree.insert("", "end", iid=str(p["id"]), values=(
                p["payment_date"], w.fmt_money(p["amount"]), p["method"] or "", p["notes"] or ""))

    def _selected_id(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def edit_selected(self):
        pid = self._selected_id()
        if not pid:
            messagebox.showinfo("No selection", "Select a payment first.")
            return
        p = self.db.get_payment(pid)
        if not p:
            return
        dlg = PaymentDialog(self, "this payment", 0, p["amount"], edit_mode=True)
        dlg.date_e.set(p["payment_date"])
        dlg.method_var.set(p["method"] or "Bank Transfer")
        dlg.notes_txt.delete("1.0", "end")
        dlg.notes_txt.insert("1.0", p["notes"] or "")
        self.wait_window(dlg)
        if dlg.result:
            self.db.update_payment(pid, **dlg.result)
            self._reload()
            if self.on_change:
                self.on_change()

    def delete_selected(self):
        pid = self._selected_id()
        if not pid:
            messagebox.showinfo("No selection", "Select a payment first.")
            return
        if messagebox.askyesno(
            "Delete payment",
            "Remove this payment? The rent record's amount paid will be "
            "reduced accordingly. Use this to undo a payment logged by mistake."
        ):
            self.db.delete_payment(pid)
            self._reload()
            if self.on_change:
                self.on_change()


class RentTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.db = app.db
        self.period = w.current_period()
        self.property_filter = tk.StringVar(value="All properties")
        self._build()
        self.refresh()

    def _build(self):
        top = w.FlowFrame(self)
        top.pack(fill="x", padx=16, pady=(16, 8))

        top.add(ttk.Button(top, text="◀", width=3, command=self.prev_month))
        self.month_label = ttk.Label(top, text="", font=("Segoe UI", 13, "bold"))
        top.add(self.month_label, pad_left=4)
        top.add(ttk.Button(top, text="▶", width=3, command=self.next_month), pad_left=4)

        top.add(ttk.Label(top, text="Property:"), pad_left=16)
        self.prop_combo = ttk.Combobox(top, textvariable=self.property_filter, width=22,
                                        state="readonly")
        top.add(self.prop_combo, pad_left=4)
        self.prop_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        top.add(ttk.Button(top, text="Generate records for this month",
                            command=self.generate_month), pad_left=16)

        # ---- grid
        columns = ("tenant", "property_unit", "due", "paid", "balance", "status", "due_date")
        tree_holder, self.tree = w.scrolled_tree(self, columns, height=18)
        headings = {
            "tenant": "Tenant", "property_unit": "Property / Unit", "due": "Amount Due",
            "paid": "Amount Paid", "balance": "Balance", "status": "Status",
            "due_date": "Due Date",
        }
        widths = {"tenant": 150, "property_unit": 170, "due": 100, "paid": 100,
                  "balance": 100, "status": 90, "due_date": 100}
        for c in columns:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c], anchor="w")
        tree_holder.pack(fill="both", expand=True, padx=16, pady=8)
        self.tree.bind("<Double-1>", lambda e: self.record_payment())

        for status, color in w.STATUS_COLORS.items():
            self.tree.tag_configure(status, background=color)

        # ---- action buttons (wraps automatically on narrow windows)
        actions = w.FlowFrame(self)
        actions.pack(fill="x", padx=16, pady=(0, 4))
        actions.add(ttk.Button(actions, text="Record Payment", style="Accent.TButton",
                                command=self.record_payment))
        actions.add(ttk.Button(actions, text="Mark Fully Paid", command=self.mark_paid), pad_left=6)
        actions.add(ttk.Button(actions, text="Mark Paid: Multiple Months",
                                command=self.bulk_mark_paid), pad_left=6)
        actions.add(ttk.Button(actions, text="View / Edit Payment History",
                                command=self.view_history), pad_left=6)
        actions.add(ttk.Button(actions, text="Edit Record", command=self.edit_due), pad_left=6)
        actions.add(ttk.Button(actions, text="Remove Record", command=self.remove_record), pad_left=6)

        summary_row = ttk.Frame(self)
        summary_row.pack(fill="x", padx=16, pady=(0, 16))
        self.summary_label = ttk.Label(summary_row, text="", foreground=w.COLOR_MUTED)
        self.summary_label.pack(side="right")

    # ------------------------------------------------------------ data
    def refresh(self):
        self.month_label.config(text=w.month_name(self.period))

        props = ["All properties"] + [p["name"] for p in self.db.list_properties()]
        self.prop_combo["values"] = props
        if self.property_filter.get() not in props:
            self.property_filter.set("All properties")

        prop_id = None
        if self.property_filter.get() != "All properties":
            for p in self.db.list_properties():
                if p["name"] == self.property_filter.get():
                    prop_id = p["id"]
                    break

        for row in self.tree.get_children():
            self.tree.delete(row)

        records = self.db.list_rent_records(period=self.period, property_id=prop_id)
        total_due = total_paid = 0
        for r in records:
            status = w.compute_status(r["amount_due"], r["amount_paid"], r["due_date"])
            balance = r["amount_due"] - r["amount_paid"]
            total_due += r["amount_due"]
            total_paid += r["amount_paid"]
            self.tree.insert("", "end", iid=str(r["id"]), values=(
                r["tenant_name"],
                f"{r['property_name'] or ''} / {r['unit_number'] or ''}".strip(" /"),
                w.fmt_money(r["amount_due"]),
                w.fmt_money(r["amount_paid"]),
                w.fmt_money(balance),
                status,
                r["due_date"] or "",
            ), tags=(status,))

        self.summary_label.config(
            text=f"Due: {w.fmt_money(total_due)}    Collected: {w.fmt_money(total_paid)}    "
                 f"Pending: {w.fmt_money(total_due - total_paid)}"
        )

    def selected_record_id(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    # ------------------------------------------------------------ actions
    def generate_month(self):
        created = self.db.generate_for_month(self.period)
        self.refresh()
        self.app.dashboard_tab.refresh()
        messagebox.showinfo(
            "Rent records generated",
            f"{created} new rent record(s) created for {w.month_name(self.period)}."
            if created else
            f"All active tenants already have rent records for {w.month_name(self.period)}."
        )

    def record_payment(self):
        rid = self.selected_record_id()
        if not rid:
            messagebox.showinfo("No selection", "Select a rent record first.")
            return
        rec = self.db.get_rent_record(rid)
        tenant = self.db.get_tenant(rec["tenant_id"])
        balance = max(rec["amount_due"] - rec["amount_paid"], 0)
        if balance <= 0:
            if not messagebox.askyesno(
                "Already fully paid",
                "This month is already marked fully paid. Record an extra payment anyway?"
            ):
                return
            balance = 0
        dlg = PaymentDialog(self, tenant["name"], balance, balance if balance > 0 else rec["amount_due"])
        self.wait_window(dlg)
        if dlg.result:
            self.db.record_payment(rid, **dlg.result)
            self.refresh()
            self.app.dashboard_tab.refresh()
            self.app.tenants_tab.refresh()

    def mark_paid(self):
        rid = self.selected_record_id()
        if not rid:
            messagebox.showinfo("No selection", "Select a rent record first.")
            return
        rec = self.db.get_rent_record(rid)
        if rec["amount_paid"] >= rec["amount_due"]:
            messagebox.showinfo("Already paid", "This rent record is already fully paid.")
            return
        today = datetime.date.today().isoformat()
        remaining = rec["amount_due"] - rec["amount_paid"]
        if messagebox.askyesno(
            "Mark fully paid",
            f"Record a payment of {w.fmt_money(remaining)} dated {today} to close this month?"
        ):
            self.db.mark_fully_paid(rid, today)
            self.refresh()
            self.app.dashboard_tab.refresh()
            self.app.tenants_tab.refresh()

    def view_history(self):
        rid = self.selected_record_id()
        if not rid:
            messagebox.showinfo("No selection", "Select a rent record first.")
            return

        def _on_change():
            self.refresh()
            self.app.dashboard_tab.refresh()
            self.app.tenants_tab.refresh()

        PaymentHistoryDialog(self, self.db, rid, on_change=_on_change)

    def bulk_mark_paid(self):
        rid = self.selected_record_id()
        if rid:
            rec = self.db.get_rent_record(rid)
            tenant = self.db.get_tenant(rec["tenant_id"])
            default_period = rec["period"]
        else:
            # No row selected - fall back to picking any tenant via a
            # quick prompt isn't available here, so ask the user to
            # select a row first (keeps the dialog scoped to one tenant).
            messagebox.showinfo(
                "No selection",
                "Select any rent record for the tenant first (any month) - "
                "this tells the app which tenant to mark paid.",
            )
            return

        dlg = BulkPaidDialog(self, tenant["name"], default_period)
        self.wait_window(dlg)
        if not dlg.result:
            return
        affected, total_paid, error = self.db.bulk_mark_paid(
            tenant["id"],
            dlg.result["start_period"],
            dlg.result["num_months"],
            dlg.result["payment_date"],
            dlg.result["method"],
            dlg.result["notes"],
        )
        if error:
            messagebox.showwarning("Couldn't mark paid", error)
            return
        self.refresh()
        self.app.dashboard_tab.refresh()
        self.app.tenants_tab.refresh()
        messagebox.showinfo(
            "Marked paid",
            f"{affected} month(s) processed for {tenant['name']}.\n"
            f"Total recorded as paid: {w.fmt_money(total_paid)}."
        )

    def edit_due(self):
        rid = self.selected_record_id()
        if not rid:
            messagebox.showinfo("No selection", "Select a rent record first.")
            return
        rec = self.db.get_rent_record(rid)

        win = tk.Toplevel(self)
        win.configure(bg=w.COLOR_BG)
        win.title("Edit rent record")
        win.resizable(False, False)
        win.grab_set()
        frm = ttk.Frame(win, padding=16)
        frm.pack()

        due_e = w.LabeledEntry(frm, "Amount due", width=22)
        due_e.set(rec["amount_due"])
        due_e.pack(fill="x", pady=4)

        paid_e = w.LabeledEntry(frm, "Amount paid", width=22)
        paid_e.set(rec["amount_paid"])
        paid_e.pack(fill="x", pady=4)
        ttk.Label(frm, text="Set this directly to fix a record marked paid\nby mistake "
                             "(e.g. back to 0). Prefer 'View / Edit\nPayment History' if you "
                             "want to edit a specific payment.",
                  foreground=w.COLOR_MUTED, justify="left").pack(anchor="w", pady=(0, 4))

        date_e = w.LabeledEntry(frm, "Due date (YYYY-MM-DD)", width=22)
        date_e.set(rec["due_date"] or "")
        date_e.pack(fill="x", pady=4)

        ttk.Label(frm, text="Notes", foreground=w.COLOR_MUTED).pack(anchor="w", pady=(4, 0))
        notes_txt = tk.Text(frm, width=22, height=2, **w.entry_colors())
        notes_txt.insert("1.0", rec["notes"] or "")
        notes_txt.pack(fill="x", pady=4)

        def save():
            try:
                due_amt = float(due_e.get())
                paid_amt = float(paid_e.get())
            except ValueError:
                messagebox.showwarning("Invalid amount", "Enter valid numbers.")
                return
            self.db.update_rent_record(
                rid, due_amt, paid_amt, date_e.get().strip(), notes_txt.get("1.0", "end").strip()
            )
            self.refresh()
            self.app.dashboard_tab.refresh()
            self.app.tenants_tab.refresh()
            win.destroy()

        btns = ttk.Frame(frm)
        btns.pack(fill="x", pady=(12, 0))
        ttk.Button(btns, text="Cancel", command=win.destroy).pack(side="right", padx=4)
        ttk.Button(btns, text="Save", style="Accent.TButton", command=save).pack(side="right")

    def remove_record(self):
        rid = self.selected_record_id()
        if not rid:
            messagebox.showinfo("No selection", "Select a rent record first.")
            return
        if messagebox.askyesno(
            "Remove rent record",
            "Remove this month's rent record (and any payments logged against it)?\n"
            "Use this to undo an accidental 'Generate' for a tenant."
        ):
            self.db.delete_rent_record(rid)
            self.refresh()
            self.app.dashboard_tab.refresh()

    def prev_month(self):
        self.period = w.shift_period(self.period, -1)
        self.refresh()

    def next_month(self):
        self.period = w.shift_period(self.period, 1)
        self.refresh()
