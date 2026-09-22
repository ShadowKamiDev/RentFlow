"""
tabs_tenants.py - manage tenants: contact info, lease dates, deposit,
and link to a unit. Monthly rent is derived from the unit's rent
periods / default rent — no separate rent field on the tenant.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime

import widgets as w
from tabs_rent import BulkPaidDialog, PaymentDialog


class TenantDialog(tk.Toplevel):
    def __init__(self, parent, db, title, tenant=None):
        super().__init__(parent)
        self.configure(bg=w.COLOR_BG)
        self.title(title)
        self.resizable(False, False)
        self.db = db
        self.result = None
        self.grab_set()

        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)

        left = ttk.Frame(frm)
        left.grid(row=0, column=0, sticky="n", padx=(0, 16))
        right = ttk.Frame(frm)
        right.grid(row=0, column=1, sticky="n")

        # ---- left column
        self.name_e = w.LabeledEntry(left, "Full name *", width=28)
        self.name_e.pack(fill="x", pady=4)
        self.phone_e = w.LabeledEntry(left, "Phone", width=28)
        self.phone_e.pack(fill="x", pady=4)
        self.email_e = w.LabeledEntry(left, "Email", width=28)
        self.email_e.pack(fill="x", pady=4)

        ttk.Label(left, text="Unit", foreground=w.COLOR_MUTED).pack(anchor="w", pady=(4, 0))
        self.unit_var = tk.StringVar()
        self.unit_map = {"— No unit assigned —": None}
        for u in db.list_units():
            label = f"{u['property_name']} / {u['unit_number']}"
            self.unit_map[label] = u["id"]
        self.unit_combo = ttk.Combobox(left, textvariable=self.unit_var, width=28,
                                        values=list(self.unit_map.keys()), state="readonly")
        self.unit_combo.pack(fill="x", pady=4)
        self.unit_combo.set("— No unit assigned —")
        self.unit_combo.bind("<<ComboboxSelected>>", self._on_unit_pick)

        # Rent preview label (read-only, shows effective rent from unit)
        self._rent_var = tk.StringVar(value="—")
        ttk.Label(left, text="Current unit rent (auto)", foreground=w.COLOR_MUTED).pack(
            anchor="w", pady=(8, 0))
        ttk.Label(left, textvariable=self._rent_var,
                  font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 4))

        # ---- right column
        self.deposit_e = w.LabeledEntry(right, "Security deposit", width=28)
        self.deposit_e.pack(fill="x", pady=4)
        self.lease_start_e = w.LabeledEntry(right, "Lease start (YYYY-MM-DD)", width=28)
        self.lease_start_e.pack(fill="x", pady=4)
        self.lease_end_e = w.LabeledEntry(right, "Lease end (YYYY-MM-DD)", width=28)
        self.lease_end_e.pack(fill="x", pady=4)

        notes_frame = ttk.Frame(frm)
        notes_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Label(notes_frame, text="Notes", foreground=w.COLOR_MUTED).pack(anchor="w")
        self.notes_txt = tk.Text(notes_frame, width=60, height=3, **w.entry_colors())
        self.notes_txt.pack(fill="x", pady=4)

        btns = ttk.Frame(frm)
        btns.grid(row=2, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(btns, text="Save", style="Accent.TButton", command=self.on_save).pack(side="right")

        if tenant:
            self.name_e.set(tenant["name"])
            self.phone_e.set(tenant["phone"])
            self.email_e.set(tenant["email"])
            self.deposit_e.set(tenant["deposit"])
            self.lease_start_e.set(tenant["lease_start"])
            self.lease_end_e.set(tenant["lease_end"])
            self.notes_txt.insert("1.0", tenant["notes"] or "")
            if tenant["unit_id"]:
                for label, uid in self.unit_map.items():
                    if uid == tenant["unit_id"]:
                        self.unit_combo.set(label)
                        self._refresh_rent_preview(tenant["unit_id"])
                        break

        self.name_e.entry.focus_set()

    def _refresh_rent_preview(self, unit_id):
        if not unit_id:
            self._rent_var.set("—")
            return
        rent = self.db.get_effective_rent_for_unit(unit_id)
        self._rent_var.set(w.fmt_money(rent) + " / month")

    def _on_unit_pick(self, event=None):
        uid = self.unit_map.get(self.unit_var.get())
        self._refresh_rent_preview(uid)

    def on_save(self):
        name = self.name_e.get().strip()
        if not name:
            messagebox.showwarning("Missing name", "Please enter the tenant's name.")
            return
        try:
            deposit = float(self.deposit_e.get() or 0)
        except ValueError:
            messagebox.showwarning("Invalid number", "Deposit must be a number.")
            return
        for date_str, label in [(self.lease_start_e.get(), "Lease start"),
                                 (self.lease_end_e.get(), "Lease end")]:
            if date_str:
                try:
                    datetime.datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    messagebox.showwarning("Invalid date", f"{label} must be in YYYY-MM-DD format.")
                    return
        self.result = {
            "unit_id":     self.unit_map.get(self.unit_var.get()),
            "name":        name,
            "phone":       self.phone_e.get().strip(),
            "email":       self.email_e.get().strip(),
            "lease_start": self.lease_start_e.get().strip(),
            "lease_end":   self.lease_end_e.get().strip(),
            "deposit":     deposit,
            "notes":       self.notes_txt.get("1.0", "end").strip(),
        }
        self.destroy()


class TenantsTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.db = app.db
        self.show_inactive = tk.BooleanVar(value=False)
        self.search_var = tk.StringVar()
        self._build()
        self.refresh()

    def _build(self):
        top = w.FlowFrame(self)
        top.pack(fill="x", padx=16, pady=(16, 8))

        top.add(ttk.Label(top, text="Search:"))
        search_entry = ttk.Entry(top, textvariable=self.search_var, width=24)
        top.add(search_entry, pad_left=4)
        search_entry.bind("<KeyRelease>", lambda e: self.refresh())

        top.add(ttk.Checkbutton(top, text="Show inactive / moved-out tenants",
                                 variable=self.show_inactive, command=self.refresh), pad_left=12)

        top.add(ttk.Button(top, text="+ Add Tenant", command=self.add_tenant), pad_left=16)

        # ---- main split: list | detail
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        left = ttk.Frame(paned)
        paned.add(left, weight=2)

        columns = ("name", "property_unit", "phone", "rent", "status")
        tree_holder, self.tree = w.scrolled_tree(left, columns, height=20)
        headings = {
            "name":          "Name",
            "property_unit": "Property / Unit",
            "phone":         "Phone",
            "rent":          "Current Rent",
            "status":        "Status",
        }
        widths = {"name": 150, "property_unit": 170, "phone": 110, "rent": 110, "status": 80}
        for c in columns:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c], anchor="w")
        tree_holder.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.show_detail())
        self.tree.tag_configure("inactive", foreground=w.COLOR_MUTED)

        right = ttk.Frame(paned)
        paned.add(right, weight=2)
        self._build_detail(right)

    def _build_detail(self, right):
        self.detail_title = ttk.Label(right, text="Select a tenant", font=("Segoe UI", 13, "bold"))
        self.detail_title.pack(anchor="w", pady=(0, 6))

        self.detail_info = ttk.Label(right, text="", justify="left")
        self.detail_info.pack(anchor="w")

        btns = w.FlowFrame(right)
        btns.pack(fill="x", pady=8)
        btns.add(ttk.Button(btns, text="Edit", command=self.edit_tenant))
        self.toggle_btn = ttk.Button(btns, text="Mark Moved Out", command=self.toggle_active)
        btns.add(self.toggle_btn, pad_left=4)
        btns.add(ttk.Button(btns, text="Delete", command=self.delete_tenant), pad_left=4)
        btns.add(ttk.Button(btns, text="Generate All Rent Records", style="Accent.TButton",
                             command=self.generate_all_records), pad_left=12)
        btns.add(ttk.Button(btns, text="Mark Paid: Multiple Months", style="Accent.TButton",
                             command=self.bulk_mark_paid), pad_left=6)

        hist_hdr = ttk.Frame(right)
        hist_hdr.pack(fill="x", pady=(12, 4))
        ttk.Label(hist_hdr, text="Payment history", font=("Segoe UI", 11, "bold")).pack(
            anchor="w")
        ttk.Label(hist_hdr, text="Select a payment below to edit or undo (delete) it.",
                  foreground=w.COLOR_MUTED).pack(anchor="w")

        columns = ("period", "date", "amount", "method", "notes")
        hist_tree_holder, self.hist_tree = w.scrolled_tree(right, columns, height=14)
        headings = {"period": "Month", "date": "Payment Date", "amount": "Amount",
                    "method": "Method", "notes": "Notes"}
        widths = {"period": 80, "date": 100, "amount": 90, "method": 110, "notes": 160}
        for c in columns:
            self.hist_tree.heading(c, text=headings[c])
            self.hist_tree.column(c, width=widths[c], anchor="w")
        hist_tree_holder.pack(fill="both", expand=True)

        hist_btns = w.FlowFrame(right)
        hist_btns.pack(fill="x", pady=(4, 0))
        hist_btns.add(ttk.Button(hist_btns, text="Edit Payment", command=self.edit_payment))
        hist_btns.add(ttk.Button(hist_btns, text="Delete Payment (undo)",
                                  command=self.delete_payment), pad_left=6)

    # ------------------------------------------------------------ data
    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        rows = self.db.list_tenants(
            active_only=not self.show_inactive.get(),
            search=self.search_var.get().strip() or None,
        )
        self.tenants_by_id = {}
        for t in rows:
            self.tenants_by_id[t["id"]] = t
            tag = "inactive" if not t["is_active"] else ""
            # Show effective current rent for the unit
            if t["unit_id"]:
                rent_display = w.fmt_money(self.db.get_effective_rent_for_unit(t["unit_id"]))
            else:
                rent_display = "—"
            self.tree.insert("", "end", iid=str(t["id"]), values=(
                t["name"],
                f"{t['property_name'] or ''} / {t['unit_number'] or ''}".strip(" /"),
                t["phone"] or "",
                rent_display,
                "Active" if t["is_active"] else "Moved out",
            ), tags=(tag,))
        self.show_detail()

    def selected_tenant(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return self.db.get_tenant(int(sel[0]))

    def show_detail(self):
        t = self.selected_tenant()
        for row in self.hist_tree.get_children():
            self.hist_tree.delete(row)
        if not t:
            self.detail_title.config(text="Select a tenant")
            self.detail_info.config(text="")
            return
        self.detail_title.config(text=t["name"])

        # Effective rent from unit
        if t["unit_id"]:
            rent_display = w.fmt_money(self.db.get_effective_rent_for_unit(t["unit_id"]))
        else:
            rent_display = "—"

        info_lines = [
            f"Unit: {t['property_name'] or '—'} / {t['unit_number'] or '—'}",
            f"Phone: {t['phone'] or '—'}    Email: {t['email'] or '—'}",
            f"Lease: {t['lease_start'] or '—'} to {t['lease_end'] or '—'}",
            f"Current rent: {rent_display}    Deposit: {w.fmt_money(t['deposit'])}",
            f"Status: {'Active' if t['is_active'] else 'Moved out on ' + (t['move_out_date'] or '?')}",
        ]
        if t["notes"]:
            info_lines.append(f"Notes: {t['notes']}")
        self.detail_info.config(text="\n".join(info_lines))
        self.toggle_btn.config(
            text="Mark Moved Out" if t["is_active"] else "Reactivate Tenant"
        )

        payments = self.db.list_payments_for_tenant(t["id"])
        for p in payments:
            self.hist_tree.insert("", "end", iid=str(p["id"]), values=(
                p["period"], p["payment_date"], w.fmt_money(p["amount"]),
                p["method"] or "", p["notes"] or "",
            ))

    # ------------------------------------------------------------ actions
    def add_tenant(self):
        dlg = TenantDialog(self, self.db, "Add Tenant")
        self.wait_window(dlg)
        if dlg.result:
            self.db.add_tenant(**dlg.result)
            self.refresh()
            self.app.refresh_all()

    def edit_tenant(self):
        t = self.selected_tenant()
        if not t:
            messagebox.showinfo("No selection", "Select a tenant first.")
            return
        dlg = TenantDialog(self, self.db, "Edit Tenant", tenant=t)
        self.wait_window(dlg)
        if dlg.result:
            self.db.update_tenant(t["id"], **dlg.result)
            self.refresh()
            self.app.refresh_all()

    def toggle_active(self):
        t = self.selected_tenant()
        if not t:
            return
        if t["is_active"]:
            today = datetime.date.today().isoformat()
            if messagebox.askyesno("Mark moved out",
                                    f"Mark {t['name']} as moved out as of {today}?"):
                self.db.set_tenant_active(t["id"], False, today)
                self.refresh()
                self.app.refresh_all()
        else:
            self.db.set_tenant_active(t["id"], True, None)
            self.refresh()
            self.app.refresh_all()

    def delete_tenant(self):
        t = self.selected_tenant()
        if not t:
            messagebox.showinfo("No selection", "Select a tenant first.")
            return
        if messagebox.askyesno(
            "Delete tenant",
            f"Permanently delete {t['name']} and ALL their rent/payment history?\n"
            "This cannot be undone.",
        ):
            self.db.delete_tenant(t["id"])
            self.refresh()
            self.app.refresh_all()

    def bulk_mark_paid(self):
        t = self.selected_tenant()
        if not t:
            messagebox.showinfo("No selection", "Select a tenant first.")
            return
        default_period = datetime.date.today().strftime("%Y-%m")
        dlg = BulkPaidDialog(self, t["name"], default_period)
        self.wait_window(dlg)
        if not dlg.result:
            return
        affected, total_paid, error = self.db.bulk_mark_paid(
            t["id"],
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
        self.app.refresh_all()
        messagebox.showinfo(
            "Marked paid",
            f"{affected} month(s) processed for {t['name']}.\n"
            f"Total recorded as paid: {w.fmt_money(total_paid)}."
        )

    def _selected_payment_id(self):
        sel = self.hist_tree.selection()
        return int(sel[0]) if sel else None

    def edit_payment(self):
        pid = self._selected_payment_id()
        if not pid:
            messagebox.showinfo("No selection", "Select a payment in the history list first.")
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
            self.refresh()
            self.app.refresh_all()

    def delete_payment(self):
        pid = self._selected_payment_id()
        if not pid:
            messagebox.showinfo("No selection", "Select a payment in the history list first.")
            return
        if messagebox.askyesno(
            "Delete payment",
            "Remove this payment? The rent record's amount paid will be "
            "reduced accordingly. Use this to undo a payment logged by mistake."
        ):
            self.db.delete_payment(pid)
            self.refresh()
            self.app.refresh_all()

    def generate_all_records(self):
        t = self.selected_tenant()
        if not t:
            messagebox.showinfo("No selection", "Select a tenant first.")
            return
        if not t["lease_start"]:
            messagebox.showwarning(
                "No lease start date",
                f"{t['name']} has no lease start date set. Edit the tenant and "
                "add one first so the app knows which month to start from.",
            )
            return
        end_desc = (
            "today" if t["is_active"] or not t["move_out_date"]
            else f"their move-out date ({t['move_out_date']})"
        )
        if not messagebox.askyesno(
            "Generate all rent records",
            f"Generate a rent record for {t['name']} for every month from their "
            f"lease start ({t['lease_start']}) through {end_desc}?\n\n"
            "Rent amounts will reflect the unit's rent history for each month.\n"
            "Existing months are left untouched — this only fills in the gaps.",
        ):
            return
        created, error = self.db.generate_for_tenant(t["id"])
        if error:
            messagebox.showwarning("Couldn't generate records", error)
            return
        self.refresh()
        self.app.refresh_all()
        messagebox.showinfo(
            "Rent records generated",
            f"{created} new rent record(s) created for {t['name']}."
            if created else
            f"{t['name']} already has rent records for every month in that range."
        )
