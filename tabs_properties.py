"""
tabs_properties.py - manage properties and the units within each one.
Also includes per-unit Rent Period management so owners can track rent
changes over time (e.g. "₹8,000 from Jan 2024 → ₹9,500 from Jul 2025").
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime

import widgets as w


class PropertyDialog(tk.Toplevel):
    def __init__(self, parent, title, name="", address="", notes=""):
        super().__init__(parent)
        self.configure(bg=w.COLOR_BG)
        self.title(title)
        self.resizable(False, False)
        self.result = None
        self.grab_set()

        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)

        self.name_e = w.LabeledEntry(frm, "Property name *", width=34)
        self.name_e.set(name)
        self.name_e.pack(fill="x", pady=4)

        self.addr_e = w.LabeledEntry(frm, "Address", width=34)
        self.addr_e.set(address)
        self.addr_e.pack(fill="x", pady=4)

        ttk.Label(frm, text="Notes", foreground=w.COLOR_MUTED).pack(anchor="w", pady=(4, 0))
        self.notes_txt = tk.Text(frm, width=34, height=3, **w.entry_colors())
        self.notes_txt.insert("1.0", notes or "")
        self.notes_txt.pack(fill="x", pady=4)

        btns = ttk.Frame(frm)
        btns.pack(fill="x", pady=(12, 0))
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(btns, text="Save", style="Accent.TButton", command=self.on_save).pack(side="right")

        self.bind("<Return>", lambda e: self.on_save())
        self.name_e.entry.focus_set()

    def on_save(self):
        name = self.name_e.get().strip()
        if not name:
            messagebox.showwarning("Missing name", "Please enter a property name.")
            return
        self.result = {
            "name":    name,
            "address": self.addr_e.get().strip(),
            "notes":   self.notes_txt.get("1.0", "end").strip(),
        }
        self.destroy()


class UnitDialog(tk.Toplevel):
    def __init__(self, parent, title, unit_number="", bedrooms="", default_rent=0, notes=""):
        super().__init__(parent)
        self.configure(bg=w.COLOR_BG)
        self.title(title)
        self.resizable(False, False)
        self.result = None
        self.grab_set()

        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)

        self.num_e = w.LabeledEntry(frm, "Unit number / name *", width=28)
        self.num_e.set(unit_number)
        self.num_e.pack(fill="x", pady=4)

        self.bed_e = w.LabeledEntry(frm, "Bedrooms / Type", width=28)
        self.bed_e.set(bedrooms)
        self.bed_e.pack(fill="x", pady=4)

        self.rent_e = w.LabeledEntry(frm, "Default monthly rent", width=28)
        self.rent_e.set(default_rent)
        self.rent_e.pack(fill="x", pady=4)

        ttk.Label(frm, text="Notes", foreground=w.COLOR_MUTED).pack(anchor="w", pady=(4, 0))
        self.notes_txt = tk.Text(frm, width=28, height=3, **w.entry_colors())
        self.notes_txt.insert("1.0", notes or "")
        self.notes_txt.pack(fill="x", pady=4)

        btns = ttk.Frame(frm)
        btns.pack(fill="x", pady=(12, 0))
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(btns, text="Save", style="Accent.TButton", command=self.on_save).pack(side="right")

        self.bind("<Return>", lambda e: self.on_save())
        self.num_e.entry.focus_set()

    def on_save(self):
        num = self.num_e.get().strip()
        if not num:
            messagebox.showwarning("Missing unit number", "Please enter a unit number or name.")
            return
        try:
            rent = float(self.rent_e.get() or 0)
        except ValueError:
            messagebox.showwarning("Invalid rent", "Default rent must be a number.")
            return
        self.result = {
            "unit_number":  num,
            "bedrooms":     self.bed_e.get().strip(),
            "default_rent": rent,
            "notes":        self.notes_txt.get("1.0", "end").strip(),
        }
        self.destroy()


class RentPeriodDialog(tk.Toplevel):
    """Dialog to add or edit a Rent Period for a unit.

    A rent period records that a unit's rent was a specific amount for a
    date range (start_date → end_date). Leaving end_date blank means the
    period is still active / open-ended.
    """

    def __init__(self, parent, unit_label, period=None):
        super().__init__(parent)
        self.configure(bg=w.COLOR_BG)
        self.title(f"Rent Period — {unit_label}")
        self.resizable(False, False)
        self.result = None
        self.grab_set()

        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text=f"Unit:  {unit_label}",
                  foreground=w.COLOR_MUTED).pack(anchor="w", pady=(0, 8))

        self.amount_e = w.LabeledEntry(frm, "Rent amount *", width=28)
        self.amount_e.pack(fill="x", pady=4)

        self.start_e = w.LabeledEntry(frm, "Effective from (YYYY-MM-DD) *", width=28)
        self.start_e.pack(fill="x", pady=4)

        self.end_e = w.LabeledEntry(frm, "Effective until (YYYY-MM-DD, blank = ongoing)", width=28)
        self.end_e.pack(fill="x", pady=4)

        ttk.Label(frm, text="Notes", foreground=w.COLOR_MUTED).pack(anchor="w", pady=(4, 0))
        self.notes_txt = tk.Text(frm, width=28, height=2, **w.entry_colors())
        self.notes_txt.pack(fill="x", pady=4)

        if period:
            self.amount_e.set(period["amount"])
            self.start_e.set(period["start_date"])
            self.end_e.set(period["end_date"] or "")
            self.notes_txt.insert("1.0", period["notes"] or "")

        btns = ttk.Frame(frm)
        btns.pack(fill="x", pady=(12, 0))
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(btns, text="Save", style="Accent.TButton", command=self.on_save).pack(side="right")

        self.amount_e.entry.focus_set()

    def on_save(self):
        try:
            amount = float(self.amount_e.get())
        except ValueError:
            messagebox.showwarning("Invalid amount", "Enter a valid rent amount.")
            return
        if amount <= 0:
            messagebox.showwarning("Invalid amount", "Rent amount must be greater than zero.")
            return
        start = self.start_e.get().strip()
        if not start:
            messagebox.showwarning("Missing date", "Please enter an effective-from date.")
            return
        try:
            datetime.datetime.strptime(start, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Invalid date", "Effective-from must be in YYYY-MM-DD format.")
            return
        end = self.end_e.get().strip() or None
        if end:
            try:
                datetime.datetime.strptime(end, "%Y-%m-%d")
            except ValueError:
                messagebox.showwarning("Invalid date",
                                       "Effective-until must be in YYYY-MM-DD format (or left blank).")
                return
        self.result = {
            "amount":     amount,
            "start_date": start,
            "end_date":   end,
            "notes":      self.notes_txt.get("1.0", "end").strip(),
        }
        self.destroy()


class PropertiesTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.db = app.db
        self._build()
        self.refresh()

    def _build(self):
        # Top-level paned: left (properties) | right (units + rent periods)
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=16, pady=16)

        # ---- left: properties list
        left = ttk.Frame(paned)
        paned.add(left, weight=1)

        ttk.Label(left, text="Properties", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.prop_list = tk.Listbox(
            left, height=20, exportselection=False,
            font=("Segoe UI", 10), activestyle="none",
            **w.entry_colors(include_cursor=False)
        )
        self.prop_list.pack(fill="both", expand=True, pady=6)
        self.prop_list.bind("<<ListboxSelect>>", lambda e: self.refresh_units())

        btns = w.FlowFrame(left)
        btns.pack(fill="x")
        btns.add(ttk.Button(btns, text="+ Add Property", command=self.add_property))
        btns.add(ttk.Button(btns, text="Edit",   command=self.edit_property), pad_left=4)
        btns.add(ttk.Button(btns, text="Delete", command=self.delete_property), pad_left=4)

        # ---- right: units (grows/shrinks with the window) stacked above
        # rent periods (fixed height). Previously this was a draggable
        # vertical PanedWindow, which meant you had to grab and drag a
        # thin sash to see both sections properly - annoying when you
        # just want both visible and usable at once. A plain stacked
        # layout keeps both permanently visible with no fiddling.
        right_pane = ttk.Frame(paned)
        paned.add(right_pane, weight=3)

        # -- rent periods section (packed first, from the bottom, so it
        # claims a fixed amount of space and the units section above it
        # simply takes whatever room is left)
        rp_frame = ttk.LabelFrame(right_pane, text="Rent History for Selected Unit")
        rp_frame.pack(side="bottom", fill="x", pady=(10, 0))

        # -- units section
        units_frame = ttk.Frame(right_pane)
        units_frame.pack(side="top", fill="both", expand=True)

        self.units_title = ttk.Label(units_frame, text="Units", font=("Segoe UI", 12, "bold"))
        self.units_title.pack(anchor="w")

        columns = ("unit", "type", "rent", "effective_rent", "tenant", "status")
        units_tree_holder, self.units_tree = w.scrolled_tree(units_frame, columns, height=10)
        headings = {
            "unit":          "Unit",
            "type":          "Bedrooms/Type",
            "rent":          "Default Rent",
            "effective_rent":"Current Rent",
            "tenant":        "Current Tenant",
            "status":        "Status",
        }
        widths = {"unit": 90, "type": 120, "rent": 100, "effective_rent": 110, "tenant": 150, "status": 80}
        for c in columns:
            self.units_tree.heading(c, text=headings[c])
            self.units_tree.column(c, width=widths[c], anchor="w")
        units_tree_holder.pack(fill="both", expand=True, pady=6)
        self.units_tree.tag_configure("vacant",   background=w.OCCUPANCY_COLORS["vacant"])
        self.units_tree.tag_configure("occupied", background=w.OCCUPANCY_COLORS["occupied"])
        self.units_tree.bind("<<TreeviewSelect>>", lambda e: self.refresh_rent_periods())

        ubtns = w.FlowFrame(units_frame)
        ubtns.pack(fill="x")
        ubtns.add(ttk.Button(ubtns, text="+ Add Unit",   command=self.add_unit))
        ubtns.add(ttk.Button(ubtns, text="Edit Unit",    command=self.edit_unit), pad_left=4)
        ubtns.add(ttk.Button(ubtns, text="Delete Unit",  command=self.delete_unit), pad_left=4)

        # -- rent periods content
        rp_top = ttk.Frame(rp_frame)
        rp_top.pack(fill="x", padx=6, pady=(6, 2))
        ttk.Label(
            rp_top,
            text="Track rent changes over time. The correct amount is used automatically when generating records.",
            foreground=w.COLOR_MUTED,
            wraplength=560,
        ).pack(side="left")

        rp_cols = ("amount", "start_date", "end_date", "notes")
        rp_tree_holder, self.rp_tree = w.scrolled_tree(rp_frame, rp_cols, height=5)
        rp_headings = {
            "amount":     "Rent Amount",
            "start_date": "Effective From",
            "end_date":   "Effective Until",
            "notes":      "Notes",
        }
        rp_widths = {"amount": 110, "start_date": 130, "end_date": 140, "notes": 200}
        for c in rp_cols:
            self.rp_tree.heading(c, text=rp_headings[c])
            self.rp_tree.column(c, width=rp_widths[c], anchor="w")
        rp_tree_holder.pack(fill="both", expand=True, padx=6, pady=4)

        rp_btns = w.FlowFrame(rp_frame)
        rp_btns.pack(fill="x", padx=6, pady=(0, 6))
        rp_btns.add(ttk.Button(rp_btns, text="+ Add Rent Period",
                    style="Accent.TButton", command=self.add_rent_period))
        rp_btns.add(ttk.Button(rp_btns, text="Edit",   command=self.edit_rent_period), pad_left=4)
        rp_btns.add(ttk.Button(rp_btns, text="Delete", command=self.delete_rent_period), pad_left=4)

    # ------------------------------------------------------------ data
    def refresh(self):
        self.prop_list.delete(0, "end")
        self.properties = self.db.list_properties()
        for p in self.properties:
            self.prop_list.insert("end", f"  {p['name']}")
        if self.properties:
            self.prop_list.selection_clear(0, "end")
            self.prop_list.selection_set(0)
        self.refresh_units()

    def selected_property(self):
        sel = self.prop_list.curselection()
        if not sel or not self.properties:
            return None
        return self.properties[sel[0]]

    def refresh_units(self):
        for row in self.units_tree.get_children():
            self.units_tree.delete(row)
        for row in self.rp_tree.get_children():
            self.rp_tree.delete(row)

        prop = self.selected_property()
        if not prop:
            self.units_title.config(text="Units")
            return
        self.units_title.config(text=f"Units — {prop['name']}")
        units = self.db.list_units(prop["id"])
        for u in units:
            tenant = self.db.current_tenant_for_unit(u["id"])
            tname  = tenant["name"] if tenant else "— vacant —"
            tag    = "occupied" if tenant else "vacant"
            # effective rent may differ from default_rent if rent_periods exist
            eff_rent = self.db.get_effective_rent_for_unit(u["id"])
            self.units_tree.insert("", "end", iid=str(u["id"]), values=(
                u["unit_number"],
                u["bedrooms"] or "",
                w.fmt_money(u["default_rent"]),
                w.fmt_money(eff_rent),
                tname,
                "Occupied" if tenant else "Vacant",
            ), tags=(tag,))

    def selected_unit_id(self):
        sel = self.units_tree.selection()
        return int(sel[0]) if sel else None

    def _selected_unit_label(self):
        uid = self.selected_unit_id()
        if not uid:
            return "unit"
        u = self.db.get_unit(uid)
        prop = self.selected_property()
        pname = prop["name"] if prop else ""
        return f"{pname} / {u['unit_number']}" if u else "unit"

    def refresh_rent_periods(self):
        for row in self.rp_tree.get_children():
            self.rp_tree.delete(row)
        uid = self.selected_unit_id()
        if not uid:
            return
        periods = self.db.list_rent_periods(uid)
        for rp in periods:
            self.rp_tree.insert("", "end", iid=str(rp["id"]), values=(
                w.fmt_money(rp["amount"]),
                rp["start_date"],
                rp["end_date"] or "— ongoing —",
                rp["notes"] or "",
            ))

    # ------------------------------------------------------------ property actions
    def add_property(self):
        dlg = PropertyDialog(self, "Add Property")
        self.wait_window(dlg)
        if dlg.result:
            self.db.add_property(**dlg.result)
            self.refresh()
            self.app.refresh_all()

    def edit_property(self):
        prop = self.selected_property()
        if not prop:
            messagebox.showinfo("No selection", "Select a property first.")
            return
        dlg = PropertyDialog(self, "Edit Property",
                             prop["name"], prop["address"] or "", prop["notes"] or "")
        self.wait_window(dlg)
        if dlg.result:
            self.db.update_property(prop["id"], **dlg.result)
            self.refresh()
            self.app.refresh_all()

    def delete_property(self):
        prop = self.selected_property()
        if not prop:
            messagebox.showinfo("No selection", "Select a property first.")
            return
        if messagebox.askyesno(
            "Delete property",
            f"Delete '{prop['name']}' and ALL its units?\n"
            "Tenants linked to those units will be kept but unassigned.\n"
            "This cannot be undone.",
        ):
            self.db.delete_property(prop["id"])
            self.refresh()
            self.app.refresh_all()

    # ------------------------------------------------------------ unit actions
    def add_unit(self):
        prop = self.selected_property()
        if not prop:
            messagebox.showinfo("No property selected", "Select (or add) a property first.")
            return
        dlg = UnitDialog(self, "Add Unit")
        self.wait_window(dlg)
        if dlg.result:
            if self._unit_number_taken(prop["id"], dlg.result["unit_number"]):
                messagebox.showwarning(
                    "Duplicate unit",
                    f"Property '{prop['name']}' already has a unit numbered "
                    f"'{dlg.result['unit_number']}'. Use a different number, "
                    "or edit the existing unit instead.",
                )
                return
            self.db.add_unit(prop["id"], **dlg.result)
            self.refresh_units()
            self.app.refresh_all()

    def edit_unit(self):
        uid = self.selected_unit_id()
        if not uid:
            messagebox.showinfo("No selection", "Select a unit first.")
            return
        u = self.db.get_unit(uid)
        dlg = UnitDialog(self, "Edit Unit", u["unit_number"], u["bedrooms"] or "",
                         u["default_rent"], u["notes"] or "")
        self.wait_window(dlg)
        if dlg.result:
            if self._unit_number_taken(u["property_id"], dlg.result["unit_number"], exclude_uid=uid):
                messagebox.showwarning(
                    "Duplicate unit",
                    f"This property already has another unit numbered "
                    f"'{dlg.result['unit_number']}'. Use a different number.",
                )
                return
            self.db.update_unit(uid, **dlg.result)
            self.refresh_units()
            self.app.refresh_all()

    def _unit_number_taken(self, property_id, unit_number, exclude_uid=None):
        """True if another unit in this property already uses this exact
        unit number (case-insensitive) - prevents accidental duplicates
        like two separate '14' units, which used to be silently allowed."""
        target = (unit_number or "").strip().lower()
        for existing in self.db.list_units(property_id):
            if exclude_uid is not None and existing["id"] == exclude_uid:
                continue
            if (existing["unit_number"] or "").strip().lower() == target:
                return True
        return False

    def delete_unit(self):
        uid = self.selected_unit_id()
        if not uid:
            messagebox.showinfo("No selection", "Select a unit first.")
            return
        tenant = self.db.current_tenant_for_unit(uid)
        msg = "Delete this unit and its entire rent history?"
        if tenant:
            msg += (f"\n\nNote: tenant '{tenant['name']}' is currently linked to it "
                    "and will be unassigned.")
        if messagebox.askyesno("Delete unit", msg):
            self.db.delete_unit(uid)
            self.refresh_units()
            self.app.refresh_all()

    # ------------------------------------------------------------ rent period actions
    def _offer_sync(self, uid, start_date, end_date, unit_label):
        """Ask if the user wants to update existing rent records for the
        months covered by the rent period, then do it and report results."""
        end_label = end_date if end_date else "current month"
        if not messagebox.askyesno(
            "Update existing rent records?",
            f"Do you also want to update the Amount Due on existing rent records\n"
            f"for {unit_label} between {start_date} and {end_label}?\n\n"
            "This will overwrite the Amount Due on records that were already generated\n"
            "for those months. Payments already recorded are not affected.",
        ):
            return
        updated = self.db.sync_rent_records_for_period(uid, start_date, end_date)
        if updated:
            messagebox.showinfo(
                "Records updated",
                f"{updated} existing rent record(s) have been updated with the new amount.",
            )
        else:
            messagebox.showinfo(
                "Nothing to update",
                "No existing rent records were found for the affected months.\n"
                "New records will use the correct amount when generated.",
            )
        self.app.refresh_all()

    def add_rent_period(self):
        uid = self.selected_unit_id()
        if not uid:
            messagebox.showinfo("No unit selected",
                                "Select a unit first, then add a rent period for it.")
            return
        dlg = RentPeriodDialog(self, self._selected_unit_label())
        self.wait_window(dlg)
        if dlg.result:
            self.db.add_rent_period(uid, **dlg.result)
            self.refresh_units()
            self.refresh_rent_periods()
            self.app.refresh_all()
            self._offer_sync(uid, dlg.result["start_date"], dlg.result.get("end_date"),
                             self._selected_unit_label())

    def edit_rent_period(self):
        sel = self.rp_tree.selection()
        if not sel:
            messagebox.showinfo("No selection", "Select a rent period first.")
            return
        rpid = int(sel[0])
        uid = self.selected_unit_id()
        if not uid:
            return
        periods = self.db.list_rent_periods(uid)
        rp = next((p for p in periods if p["id"] == rpid), None)
        if not rp:
            return
        dlg = RentPeriodDialog(self, self._selected_unit_label(), period=rp)
        self.wait_window(dlg)
        if dlg.result:
            self.db.update_rent_period(rpid, **dlg.result)
            self.refresh_units()
            self.refresh_rent_periods()
            self.app.refresh_all()
            self._offer_sync(uid, dlg.result["start_date"], dlg.result.get("end_date"),
                             self._selected_unit_label())

    def delete_rent_period(self):
        sel = self.rp_tree.selection()
        if not sel:
            messagebox.showinfo("No selection", "Select a rent period first.")
            return
        if messagebox.askyesno(
            "Delete rent period",
            "Remove this rent period entry?\n"
            "Existing rent records already generated are not affected.",
        ):
            self.db.delete_rent_period(int(sel[0]))
            self.refresh_units()
            self.refresh_rent_periods()
            self.app.refresh_all()
