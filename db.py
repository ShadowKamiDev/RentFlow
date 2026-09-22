"""
db.py - Database access layer for the Tenant & Rent Manager app.

Uses a local SQLite file so the app works completely offline with
no setup required. All schema creation and queries live here so the
UI code never has to write raw SQL.
"""

import sqlite3
import os
import sys
import json
import re
import datetime
import shutil

DB_FILENAME = "tenant_manager.db"
EXPORT_FILENAME = "data_export.json"
SETTINGS_FILENAME = "settings.json"
DATA_FOLDER_NAME = "AppData"


def _natural_key(value):
    """Sort key that treats digit runs as numbers, so unit numbers like
    '2', '3', '10', '14' sort in the order a person expects (2, 3, 10, 14)
    instead of plain text order (10, 11, 12, 13, 14, 14, 2, 3, 4) - which
    is what a plain SQL 'ORDER BY unit_number' gives you, since unit
    numbers are stored as text (units can be named '2A', 'B12', etc, so a
    numbers-only column wouldn't work)."""
    s = str(value or "")
    return [int(part) if part.isdigit() else part.lower()
            for part in re.split(r"(\d+)", s)]


def _sort_rows(rows, *key_funcs):
    """Stable multi-key sort over sqlite3.Row results. key_funcs are given
    most-significant first (e.g. property name, then unit number); applied
    least-significant first internally since Python's sort is stable."""
    rows = list(rows)
    for key_func in reversed(key_funcs):
        rows.sort(key=key_func)
    return rows


def _app_dir():
    """Folder the running script/executable lives in (works both for a
    plain .py run and for a PyInstaller --onefile build)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def default_data_dir():
    """Keep the data folder right next to the app itself (not in the
    user's home folder) so that copying/moving the whole app folder to
    a new PC or a new setup brings the data along automatically. Falls
    back to a folder in the user's home directory if the app's own
    folder isn't writable (e.g. installed under Program Files)."""
    candidate = os.path.join(_app_dir(), DATA_FOLDER_NAME)
    try:
        os.makedirs(candidate, exist_ok=True)
        probe = os.path.join(candidate, ".write_test")
        with open(probe, "w") as f:
            f.write("ok")
        os.remove(probe)
        return candidate
    except Exception:
        home = os.path.expanduser("~")
        folder = os.path.join(home, "TenantManagerData")
        os.makedirs(folder, exist_ok=True)
        return folder


def default_db_path():
    return os.path.join(default_data_dir(), DB_FILENAME)


SCHEMA = """
CREATE TABLE IF NOT EXISTS properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT,
    notes TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,
    unit_number TEXT NOT NULL,
    bedrooms TEXT,
    default_rent REAL DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS rent_periods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    notes TEXT,
    created_at TEXT,
    FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tenants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id INTEGER,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    lease_start TEXT,
    lease_end TEXT,
    monthly_rent REAL DEFAULT 0,
    deposit REAL DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    move_out_date TEXT,
    notes TEXT,
    created_at TEXT,
    FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS rent_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL,
    period TEXT NOT NULL,
    amount_due REAL NOT NULL DEFAULT 0,
    amount_paid REAL NOT NULL DEFAULT 0,
    due_date TEXT,
    notes TEXT,
    UNIQUE(tenant_id, period),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rent_record_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    payment_date TEXT NOT NULL,
    method TEXT,
    notes TEXT,
    FOREIGN KEY (rent_record_id) REFERENCES rent_records(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER,
    category TEXT,
    amount REAL NOT NULL,
    expense_date TEXT,
    notes TEXT,
    FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE SET NULL
);
"""


class Database:
    def __init__(self, path=None):
        self.path = path or default_db_path()
        self.data_dir = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(self.data_dir, exist_ok=True)
        self.export_path = os.path.join(self.data_dir, EXPORT_FILENAME)
        self.settings_path = os.path.join(self.data_dir, SETTINGS_FILENAME)

        db_existed = os.path.exists(self.path)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()

        if not db_existed:
            self._import_json_if_present()

    def _init_schema(self):
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # ---------------------------------------------------------- helpers
    def _now(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def backup_to(self, dest_path):
        self.conn.commit()
        shutil.copy(self.path, dest_path)

    def restore_from(self, src_path):
        self.conn.close()
        shutil.copy(src_path, self.path)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._export_json()

    # ---------------------------------------------------------- auto-export
    def _export_json(self):
        try:
            data = {
                "exported_at": self._now(),
                "properties":   [dict(r) for r in self.conn.execute("SELECT * FROM properties")],
                "units":        [dict(r) for r in self.conn.execute("SELECT * FROM units")],
                "rent_periods": [dict(r) for r in self.conn.execute("SELECT * FROM rent_periods")],
                "tenants":      [dict(r) for r in self.conn.execute("SELECT * FROM tenants")],
                "rent_records": [dict(r) for r in self.conn.execute("SELECT * FROM rent_records")],
                "payments":     [dict(r) for r in self.conn.execute("SELECT * FROM payments")],
                "expenses":     [dict(r) for r in self.conn.execute("SELECT * FROM expenses")],
            }
            tmp_path = self.export_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, self.export_path)
        except Exception:
            pass

    def _import_json_if_present(self):
        if not os.path.exists(self.export_path):
            return
        try:
            with open(self.export_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return

        def insert_many(table, rows):
            if not rows:
                return
            cols = list(rows[0].keys())
            placeholders = ",".join(["?"] * len(cols))
            col_list = ",".join(cols)
            for row in rows:
                self.conn.execute(
                    f"INSERT OR IGNORE INTO {table} ({col_list}) VALUES ({placeholders})",
                    [row.get(c) for c in cols],
                )

        insert_many("properties",   data.get("properties", []))
        insert_many("units",        data.get("units", []))
        insert_many("rent_periods", data.get("rent_periods", []))
        insert_many("tenants",      data.get("tenants", []))
        insert_many("rent_records", data.get("rent_records", []))
        insert_many("payments",     data.get("payments", []))
        insert_many("expenses",     data.get("expenses", []))
        self.conn.commit()

    # ---------------------------------------------------------- settings
    def load_settings(self):
        defaults = {"dark_mode": False}
        try:
            with open(self.settings_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            defaults.update(saved)
        except Exception:
            pass
        return defaults

    def save_settings(self, settings):
        try:
            tmp_path = self.settings_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
            os.replace(tmp_path, self.settings_path)
        except Exception:
            pass

    # ---------------------------------------------------------- properties
    def add_property(self, name, address="", notes=""):
        cur = self.conn.execute(
            "INSERT INTO properties (name, address, notes, created_at) VALUES (?,?,?,?)",
            (name, address, notes, self._now()),
        )
        self.conn.commit()
        self._export_json()
        return cur.lastrowid

    def update_property(self, pid, name, address, notes):
        self.conn.execute(
            "UPDATE properties SET name=?, address=?, notes=? WHERE id=?",
            (name, address, notes, pid),
        )
        self.conn.commit()
        self._export_json()

    def delete_property(self, pid):
        self.conn.execute("DELETE FROM properties WHERE id=?", (pid,))
        self.conn.commit()
        self._export_json()

    def list_properties(self):
        return self.conn.execute("SELECT * FROM properties ORDER BY name").fetchall()

    def get_property(self, pid):
        return self.conn.execute("SELECT * FROM properties WHERE id=?", (pid,)).fetchone()

    # ---------------------------------------------------------- units
    def add_unit(self, property_id, unit_number, bedrooms="", default_rent=0, notes=""):
        cur = self.conn.execute(
            "INSERT INTO units (property_id, unit_number, bedrooms, default_rent, notes) "
            "VALUES (?,?,?,?,?)",
            (property_id, unit_number, bedrooms, default_rent, notes),
        )
        self.conn.commit()
        self._export_json()
        return cur.lastrowid

    def update_unit(self, uid, unit_number, bedrooms, default_rent, notes):
        self.conn.execute(
            "UPDATE units SET unit_number=?, bedrooms=?, default_rent=?, notes=? WHERE id=?",
            (unit_number, bedrooms, default_rent, notes, uid),
        )
        # Also sync monthly_rent of active tenant to new default if no rent_period covers today
        tenant = self.current_tenant_for_unit(uid)
        if tenant:
            today = datetime.date.today().isoformat()
            active_rp = self._get_rent_period_for_unit_on_date(uid, today)
            effective = active_rp["amount"] if active_rp else default_rent
            self.conn.execute(
                "UPDATE tenants SET monthly_rent=? WHERE id=?",
                (effective, tenant["id"]),
            )
        self.conn.commit()
        self._export_json()

    def delete_unit(self, uid):
        self.conn.execute("DELETE FROM units WHERE id=?", (uid,))
        self.conn.commit()
        self._export_json()

    def list_units(self, property_id=None):
        if property_id:
            rows = self.conn.execute(
                "SELECT * FROM units WHERE property_id=?", (property_id,)
            ).fetchall()
            return _sort_rows(rows, lambda r: _natural_key(r["unit_number"]))
        rows = self.conn.execute(
            "SELECT units.*, properties.name as property_name FROM units "
            "JOIN properties ON properties.id = units.property_id"
        ).fetchall()
        return _sort_rows(
            rows,
            lambda r: (r["property_name"] or "").lower(),
            lambda r: _natural_key(r["unit_number"]),
        )

    def get_unit(self, uid):
        return self.conn.execute("SELECT * FROM units WHERE id=?", (uid,)).fetchone()

    def current_tenant_for_unit(self, unit_id):
        return self.conn.execute(
            "SELECT * FROM tenants WHERE unit_id=? AND is_active=1", (unit_id,)
        ).fetchone()

    # ---------------------------------------------------------- rent periods
    def _get_rent_period_for_unit_on_date(self, unit_id, date_str):
        """Return the single rent_periods row active on date_str (YYYY-MM-DD),
        or None if none defined."""
        return self.conn.execute(
            "SELECT * FROM rent_periods "
            "WHERE unit_id=? AND start_date<=? "
            "AND (end_date IS NULL OR end_date>=?) "
            "ORDER BY start_date DESC LIMIT 1",
            (unit_id, date_str, date_str),
        ).fetchone()

    def get_rent_for_unit_period(self, unit_id, period):
        """Return the effective monthly rent amount for a unit in a given
        YYYY-MM period. Looks up rent_periods first, falls back to
        unit.default_rent."""
        # Use the first day of the period for the lookup
        date_str = f"{period}-01"
        rp = self._get_rent_period_for_unit_on_date(unit_id, date_str)
        if rp:
            return rp["amount"]
        unit = self.get_unit(unit_id)
        if unit:
            return unit["default_rent"] or 0
        return 0

    def list_rent_periods(self, unit_id):
        return self.conn.execute(
            "SELECT * FROM rent_periods WHERE unit_id=? ORDER BY start_date DESC",
            (unit_id,),
        ).fetchall()

    def add_rent_period(self, unit_id, amount, start_date, end_date=None, notes=""):
        cur = self.conn.execute(
            "INSERT INTO rent_periods (unit_id, amount, start_date, end_date, notes, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (unit_id, amount, start_date, end_date or None, notes, self._now()),
        )
        self.conn.commit()
        self._export_json()
        return cur.lastrowid

    def update_rent_period(self, rpid, amount, start_date, end_date=None, notes=""):
        self.conn.execute(
            "UPDATE rent_periods SET amount=?, start_date=?, end_date=?, notes=? WHERE id=?",
            (amount, start_date, end_date or None, notes, rpid),
        )
        self.conn.commit()
        self._export_json()

    def delete_rent_period(self, rpid):
        self.conn.execute("DELETE FROM rent_periods WHERE id=?", (rpid,))
        self.conn.commit()
        self._export_json()

    def sync_rent_records_for_period(self, unit_id, start_date, end_date=None, due_day=5):
        """Update amount_due on all existing rent records that fall within the
        given rent period's date range for the given unit.

        Only records that already exist are touched — no new records are created.
        Returns the number of rent records updated."""
        sy, sm = int(start_date[:4]), int(start_date[5:7])
        start_idx = sy * 12 + (sm - 1)

        if end_date:
            ey, em = int(end_date[:4]), int(end_date[5:7])
            end_idx = ey * 12 + (em - 1)
        else:
            today = datetime.date.today()
            end_idx = today.year * 12 + (today.month - 1)

        updated = 0
        idx = start_idx
        while idx <= end_idx:
            yy, mm = divmod(idx, 12)
            period = f"{yy:04d}-{mm + 1:02d}"

            amount = self.get_rent_for_unit_period(unit_id, period)
            if not amount:
                idx += 1
                continue

            rows = self.conn.execute(
                "SELECT rent_records.id FROM rent_records "
                "JOIN tenants ON tenants.id = rent_records.tenant_id "
                "WHERE tenants.unit_id=? AND rent_records.period=?",
                (unit_id, period),
            ).fetchall()
            for row in rows:
                self.conn.execute(
                    "UPDATE rent_records SET amount_due=? WHERE id=?",
                    (amount, row["id"]),
                )
                updated += 1
            idx += 1

        if updated:
            self.conn.commit()
            self._export_json()
        return updated

    def get_effective_rent_for_unit(self, unit_id):
        """Return the rent currently in effect for a unit (today's date)."""
        today = datetime.date.today().isoformat()
        rp = self._get_rent_period_for_unit_on_date(unit_id, today)
        if rp:
            return rp["amount"]
        unit = self.get_unit(unit_id)
        return unit["default_rent"] if unit else 0

    # ---------------------------------------------------------- tenants
    def add_tenant(self, unit_id, name, phone, email, lease_start, lease_end,
                   deposit, notes):
        # Derive monthly_rent from unit (current effective rent)
        monthly_rent = self.get_effective_rent_for_unit(unit_id) if unit_id else 0
        cur = self.conn.execute(
            "INSERT INTO tenants (unit_id, name, phone, email, lease_start, lease_end, "
            "monthly_rent, deposit, is_active, notes, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,1,?,?)",
            (unit_id, name, phone, email, lease_start, lease_end,
             monthly_rent, deposit, notes, self._now()),
        )
        self.conn.commit()
        self._export_json()
        return cur.lastrowid

    def update_tenant(self, tid, unit_id, name, phone, email, lease_start, lease_end,
                      deposit, notes):
        # Refresh monthly_rent from the unit's current effective rent
        monthly_rent = self.get_effective_rent_for_unit(unit_id) if unit_id else 0
        self.conn.execute(
            "UPDATE tenants SET unit_id=?, name=?, phone=?, email=?, lease_start=?, "
            "lease_end=?, monthly_rent=?, deposit=?, notes=? WHERE id=?",
            (unit_id, name, phone, email, lease_start, lease_end,
             monthly_rent, deposit, notes, tid),
        )
        self.conn.commit()
        self._export_json()

    def set_tenant_active(self, tid, active, move_out_date=None):
        self.conn.execute(
            "UPDATE tenants SET is_active=?, move_out_date=? WHERE id=?",
            (1 if active else 0, move_out_date, tid),
        )
        self.conn.commit()
        self._export_json()

    def delete_tenant(self, tid):
        self.conn.execute("DELETE FROM tenants WHERE id=?", (tid,))
        self.conn.commit()
        self._export_json()

    def list_tenants(self, active_only=False, property_id=None, search=None):
        q = (
            "SELECT tenants.*, units.unit_number, properties.name as property_name, "
            "properties.id as property_id "
            "FROM tenants "
            "LEFT JOIN units ON units.id = tenants.unit_id "
            "LEFT JOIN properties ON properties.id = units.property_id WHERE 1=1"
        )
        params = []
        if active_only:
            q += " AND tenants.is_active=1"
        if property_id:
            q += " AND properties.id=?"
            params.append(property_id)
        if search:
            q += " AND (tenants.name LIKE ? OR tenants.phone LIKE ? OR tenants.email LIKE ?)"
            like = f"%{search}%"
            params += [like, like, like]
        q += " ORDER BY tenants.is_active DESC"
        rows = self.conn.execute(q, params).fetchall()
        return _sort_rows(
            rows,
            lambda r: 0 if r["is_active"] else 1,
            lambda r: (r["property_name"] or "").lower(),
            lambda r: _natural_key(r["unit_number"]),
        )

    def get_tenant(self, tid):
        return self.conn.execute(
            "SELECT tenants.*, units.unit_number, properties.name as property_name, "
            "units.default_rent, units.id as unit_id_ref "
            "FROM tenants "
            "LEFT JOIN units ON units.id = tenants.unit_id "
            "LEFT JOIN properties ON properties.id = units.property_id "
            "WHERE tenants.id=?",
            (tid,),
        ).fetchone()

    # ---------------------------------------------------------- rent records
    def ensure_rent_record(self, tenant_id, period, amount_due, due_date=None):
        """Create the rent record for a tenant/period if it doesn't exist yet."""
        existing = self.conn.execute(
            "SELECT * FROM rent_records WHERE tenant_id=? AND period=?",
            (tenant_id, period),
        ).fetchone()
        if existing:
            return existing["id"], False
        cur = self.conn.execute(
            "INSERT INTO rent_records (tenant_id, period, amount_due, amount_paid, due_date) "
            "VALUES (?,?,?,0,?)",
            (tenant_id, period, amount_due, due_date),
        )
        self.conn.commit()
        return cur.lastrowid, True

    def generate_for_month(self, period, due_day=5, only_active=True):
        """Generate rent records for every (active) tenant for the given period.
        Uses the rent_period-aware amount for each tenant's unit.
        Returns the number of new records created."""
        tenants = self.list_tenants(active_only=only_active)
        created = 0
        due_date = f"{period}-{due_day:02d}"
        for t in tenants:
            # Determine the correct rent for this period
            if t["unit_id"]:
                amount = self.get_rent_for_unit_period(t["unit_id"], period)
            else:
                amount = t["monthly_rent"] or 0
            if not amount:
                continue
            _, was_created = self.ensure_rent_record(
                t["id"], period, amount, due_date
            )
            if was_created:
                created += 1
        if created:
            self._export_json()
        return created

    def list_rent_records(self, period=None, tenant_id=None, property_id=None):
        q = (
            "SELECT rent_records.*, tenants.name as tenant_name, tenants.is_active, "
            "units.unit_number, properties.name as property_name, properties.id as pid "
            "FROM rent_records "
            "JOIN tenants ON tenants.id = rent_records.tenant_id "
            "LEFT JOIN units ON units.id = tenants.unit_id "
            "LEFT JOIN properties ON properties.id = units.property_id WHERE 1=1"
        )
        params = []
        if period:
            q += " AND rent_records.period=?"
            params.append(period)
        if tenant_id:
            q += " AND rent_records.tenant_id=?"
            params.append(tenant_id)
        if property_id:
            q += " AND properties.id=?"
            params.append(property_id)
        q += " ORDER BY rent_records.period DESC"
        rows = self.conn.execute(q, params).fetchall()
        # Multi-key stable sort: least-significant first, then most
        # significant last (as reverse=True, which stays stable for ties).
        rows = sorted(rows, key=lambda r: _natural_key(r["unit_number"]))
        rows = sorted(rows, key=lambda r: (r["property_name"] or "").lower())
        rows = sorted(rows, key=lambda r: r["period"] or "", reverse=True)
        return rows

    def get_rent_record(self, rid):
        return self.conn.execute("SELECT * FROM rent_records WHERE id=?", (rid,)).fetchone()

    def update_rent_record_due(self, rid, amount_due, due_date, notes):
        # Kept for backward compatibility - leaves amount_paid untouched.
        rec = self.get_rent_record(rid)
        self.update_rent_record(
            rid, amount_due, rec["amount_paid"] if rec else 0, due_date, notes
        )

    def update_rent_record(self, rid, amount_due, amount_paid, due_date, notes):
        """Directly set both amount_due and amount_paid on a rent record.
        Use this (rather than record_payment) to correct a mistake, e.g.
        a record that was marked paid by accident - just set amount_paid
        back to 0 (or whatever it should be)."""
        self.conn.execute(
            "UPDATE rent_records SET amount_due=?, amount_paid=?, due_date=?, notes=? WHERE id=?",
            (amount_due, amount_paid, due_date, notes, rid),
        )
        self.conn.commit()
        self._export_json()

    def delete_rent_record(self, rid):
        self.conn.execute("DELETE FROM rent_records WHERE id=?", (rid,))
        self.conn.commit()
        self._export_json()

    def all_periods(self):
        rows = self.conn.execute(
            "SELECT DISTINCT period FROM rent_records ORDER BY period DESC"
        ).fetchall()
        return [r["period"] for r in rows]

    # ---------------------------------------------------------- payments
    def record_payment(self, rent_record_id, amount, payment_date, method="", notes=""):
        self.conn.execute(
            "INSERT INTO payments (rent_record_id, amount, payment_date, method, notes) "
            "VALUES (?,?,?,?,?)",
            (rent_record_id, amount, payment_date, method, notes),
        )
        self.conn.execute(
            "UPDATE rent_records SET amount_paid = amount_paid + ? WHERE id=?",
            (amount, rent_record_id),
        )
        self.conn.commit()
        self._export_json()

    def mark_fully_paid(self, rent_record_id, payment_date, method="Full payment"):
        rec = self.get_rent_record(rent_record_id)
        remaining = round(rec["amount_due"] - rec["amount_paid"], 2)
        if remaining > 0:
            self.record_payment(rent_record_id, remaining, payment_date, method, "Marked as fully paid")

    def list_payments_for_record(self, rent_record_id):
        return self.conn.execute(
            "SELECT * FROM payments WHERE rent_record_id=? ORDER BY payment_date",
            (rent_record_id,),
        ).fetchall()

    def list_payments_for_tenant(self, tenant_id):
        return self.conn.execute(
            "SELECT payments.*, rent_records.period FROM payments "
            "JOIN rent_records ON rent_records.id = payments.rent_record_id "
            "WHERE rent_records.tenant_id=? ORDER BY payments.payment_date DESC",
            (tenant_id,),
        ).fetchall()

    def delete_payment(self, payment_id):
        row = self.conn.execute(
            "SELECT * FROM payments WHERE id=?", (payment_id,)
        ).fetchone()
        if not row:
            return
        self.conn.execute(
            "UPDATE rent_records SET amount_paid = amount_paid - ? WHERE id=?",
            (row["amount"], row["rent_record_id"]),
        )
        self.conn.execute("DELETE FROM payments WHERE id=?", (payment_id,))
        self.conn.commit()
        self._export_json()

    def get_payment(self, payment_id):
        return self.conn.execute(
            "SELECT * FROM payments WHERE id=?", (payment_id,)
        ).fetchone()

    def update_payment(self, payment_id, amount, payment_date, method="", notes=""):
        """Edit an existing payment (amount/date/method/notes) and keep
        the parent rent record's amount_paid in sync. Use this to fix a
        payment that was logged with the wrong amount instead of
        deleting and re-adding it."""
        row = self.conn.execute(
            "SELECT * FROM payments WHERE id=?", (payment_id,)
        ).fetchone()
        if not row:
            return
        delta = amount - row["amount"]
        self.conn.execute(
            "UPDATE payments SET amount=?, payment_date=?, method=?, notes=? WHERE id=?",
            (amount, payment_date, method, notes, payment_id),
        )
        self.conn.execute(
            "UPDATE rent_records SET amount_paid = amount_paid + ? WHERE id=?",
            (delta, row["rent_record_id"]),
        )
        self.conn.commit()
        self._export_json()

    # ---------------------------------------------------------- expenses
    def add_expense(self, property_id, category, amount, expense_date, notes=""):
        cur = self.conn.execute(
            "INSERT INTO expenses (property_id, category, amount, expense_date, notes) "
            "VALUES (?,?,?,?,?)",
            (property_id, category, amount, expense_date, notes),
        )
        self.conn.commit()
        self._export_json()
        return cur.lastrowid

    def list_expenses(self, property_id=None):
        q = (
            "SELECT expenses.*, properties.name as property_name FROM expenses "
            "LEFT JOIN properties ON properties.id = expenses.property_id WHERE 1=1"
        )
        params = []
        if property_id:
            q += " AND expenses.property_id=?"
            params.append(property_id)
        q += " ORDER BY expenses.expense_date DESC"
        return self.conn.execute(q, params).fetchall()

    def delete_expense(self, eid):
        self.conn.execute("DELETE FROM expenses WHERE id=?", (eid,))
        self.conn.commit()
        self._export_json()

    # ---------------------------------------------------------- dashboard / stats
    def month_summary(self, period):
        rows = self.list_rent_records(period=period)
        total_due = sum(r["amount_due"] for r in rows)
        total_paid = sum(r["amount_paid"] for r in rows)
        paid_count = sum(1 for r in rows if r["amount_paid"] >= r["amount_due"] and r["amount_due"] > 0)
        partial_count = sum(1 for r in rows if 0 < r["amount_paid"] < r["amount_due"])
        unpaid_count = sum(1 for r in rows if r["amount_paid"] == 0)
        today = datetime.date.today().isoformat()
        overdue = [
            r for r in rows
            if r["amount_paid"] < r["amount_due"] and r["due_date"] and r["due_date"] < today
        ]
        return {
            "total_due":     total_due,
            "total_paid":    total_paid,
            "total_pending": total_due - total_paid,
            "paid_count":    paid_count,
            "partial_count": partial_count,
            "unpaid_count":  unpaid_count,
            "overdue":       overdue,
            "records":       rows,
        }

    def overdue_tenant_count(self):
        """Count tenants who are overdue on ANY rent record, not just the
        record for whichever month happens to be selected on the
        Dashboard. A tenant can be overdue on last month's rent while
        this month's record isn't due yet - that still needs to show up
        as 'Overdue Tenants'."""
        today = datetime.date.today().isoformat()
        rows = self.conn.execute(
            "SELECT DISTINCT rent_records.tenant_id FROM rent_records "
            "JOIN tenants ON tenants.id = rent_records.tenant_id "
            "WHERE rent_records.amount_paid < rent_records.amount_due "
            "AND rent_records.due_date IS NOT NULL "
            "AND rent_records.due_date < ? "
            "AND tenants.is_active = 1",
            (today,),
        ).fetchall()
        return len(rows)

    def occupancy_summary(self):
        total_units = self.conn.execute("SELECT COUNT(*) c FROM units").fetchone()["c"]
        occupied = self.conn.execute(
            "SELECT COUNT(DISTINCT unit_id) c FROM tenants WHERE is_active=1 AND unit_id IS NOT NULL"
        ).fetchone()["c"]
        return total_units, occupied

    def year_collection_summary(self, year):
        rows = self.conn.execute(
            "SELECT period, SUM(amount_due) due, SUM(amount_paid) paid FROM rent_records "
            "WHERE period LIKE ? GROUP BY period ORDER BY period",
            (f"{year}-%",),
        ).fetchall()
        return rows

    def tenant_year_summary(self, year):
        rows = self.conn.execute(
            "SELECT tenants.id as tenant_id, tenants.name as tenant_name, "
            "tenants.is_active, properties.name as property_name, "
            "units.unit_number, "
            "SUM(rent_records.amount_due) as due, "
            "SUM(rent_records.amount_paid) as paid, "
            "COUNT(rent_records.id) as records_count "
            "FROM rent_records "
            "JOIN tenants ON tenants.id = rent_records.tenant_id "
            "LEFT JOIN units ON units.id = tenants.unit_id "
            "LEFT JOIN properties ON properties.id = units.property_id "
            "WHERE rent_records.period LIKE ? "
            "GROUP BY tenants.id",
            (f"{year}-%",),
        ).fetchall()
        return _sort_rows(
            rows,
            lambda r: (r["property_name"] or "").lower(),
            lambda r: _natural_key(r["unit_number"]),
            lambda r: (r["tenant_name"] or "").lower(),
        )

    def generate_for_tenant(self, tenant_id, due_day=5):
        """Backfill rent records for a single tenant for every month from
        their lease_start up to the current month (or up to their
        move_out_date if they're no longer active). Uses rent_period-aware
        amounts for each month. Returns (created_count, error_message_or_None)."""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return 0, "Tenant not found."
        if not tenant["lease_start"]:
            return 0, "This tenant has no lease start date set."
        try:
            start_period = tenant["lease_start"][:7]
            sy, sm = (int(x) for x in start_period.split("-"))
        except Exception:
            return 0, "Lease start date is not in a valid YYYY-MM-DD format."

        if tenant["is_active"] or not tenant["move_out_date"]:
            end_period = datetime.date.today().strftime("%Y-%m")
        else:
            end_period = tenant["move_out_date"][:7]
        try:
            ey, em = (int(x) for x in end_period.split("-"))
        except Exception:
            end_period = datetime.date.today().strftime("%Y-%m")
            ey, em = (int(x) for x in end_period.split("-"))

        start_idx = sy * 12 + (sm - 1)
        end_idx   = ey * 12 + (em - 1)
        if end_idx < start_idx:
            return 0, "Lease start date is after the end of the range - nothing to generate."

        created = 0
        idx = start_idx
        while idx <= end_idx:
            yy, mm = divmod(idx, 12)
            period = f"{yy:04d}-{mm + 1:02d}"
            due_date = f"{period}-{due_day:02d}"

            # Per-period rent lookup
            if tenant["unit_id"]:
                amount = self.get_rent_for_unit_period(tenant["unit_id"], period)
            else:
                amount = tenant["monthly_rent"] or 0

            if amount:
                _, was_created = self.ensure_rent_record(
                    tenant_id, period, amount, due_date
                )
                if was_created:
                    created += 1
            idx += 1

        if created:
            self._export_json()
        return created, None

    def bulk_mark_paid(self, tenant_id, start_period, num_months,
                        payment_date, method="Bulk payment", notes="",
                        due_day=5):
        """Create (if needed) and fully pay a tenant's rent record for
        `num_months` consecutive periods starting at start_period
        (YYYY-MM). Lets you record several months of rent as paid in
        one go instead of one month at a time.

        Returns (months_affected, total_amount_paid, error_or_None)."""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return 0, 0, "Tenant not found."
        try:
            sy, sm = (int(x) for x in start_period.split("-"))
        except Exception:
            return 0, 0, "Start month must be in YYYY-MM format."
        if num_months < 1:
            return 0, 0, "Number of months must be at least 1."

        start_idx = sy * 12 + (sm - 1)
        affected = 0
        total_paid = 0.0
        for i in range(num_months):
            yy, mm = divmod(start_idx + i, 12)
            period = f"{yy:04d}-{mm + 1:02d}"
            due_date = f"{period}-{due_day:02d}"

            if tenant["unit_id"]:
                amount = self.get_rent_for_unit_period(tenant["unit_id"], period)
            else:
                amount = tenant["monthly_rent"] or 0
            if not amount:
                continue

            rid, _ = self.ensure_rent_record(tenant_id, period, amount, due_date)
            rec = self.get_rent_record(rid)
            remaining = round(rec["amount_due"] - rec["amount_paid"], 2)
            if remaining > 0:
                self.record_payment(rid, remaining, payment_date, method,
                                     notes or "Bulk mark-paid")
                total_paid += remaining
            affected += 1

        if affected:
            self._export_json()
        return affected, total_paid, None
