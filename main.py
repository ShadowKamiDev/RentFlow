"""
RentFlow
========
A desktop application (Tkinter + SQLite) for tracking tenants, units,
properties and monthly rent payments.

Run with:  python3 main.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
import csv
import os
import sys

from db import Database, default_db_path
import widgets as w


APP_TITLE = "RentFlow"


def _app_dir():
    """Folder this script (or the frozen .exe) lives in."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1220x740")
        self.minsize(760, 480)
        self._set_icon()

        self.db = Database()

        # Load saved preferences and apply the theme before any widgets are built.
        self.settings = self.db.load_settings()
        w.set_mode("dark" if self.settings.get("dark_mode") else "light")

        self._setup_style()
        self._build_menu()
        self._build_tabs()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ------------------------------------------------------------ setup
    def _set_icon(self):
        base_dir = getattr(sys, "_MEIPASS", _app_dir())
        ico_path = os.path.join(base_dir, "icon.ico")
        png_path = os.path.join(base_dir, "icon.png")

        if os.name == "nt":
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                    "RentFlow.App"
                )
            except Exception:
                pass

        if os.name == "nt" and os.path.exists(ico_path):
            try:
                self.iconbitmap(default=ico_path)
            except Exception:
                pass

        if os.path.exists(png_path):
            try:
                self._icon_image = tk.PhotoImage(file=png_path)
                self.iconphoto(True, self._icon_image)
            except Exception:
                pass

    def _setup_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        t = w.theme_colors()
        bg       = t["BG"]
        card     = t["CARD"]
        text     = t["TEXT"]
        muted    = t["MUTED"]
        primary  = t["PRIMARY"]
        primary_dark = t["PRIMARY_DARK"]
        input_bg = t["INPUT_BG"]
        border   = t["BORDER"]
        danger   = t["DANGER"]
        success  = t["SUCCESS"]

        self.configure(bg=bg)

        # ---- base
        style.configure(".",
                         font=("Segoe UI", 10),
                         background=bg,
                         foreground=text,
                         bordercolor=border,
                         focuscolor=primary)

        # ---- frames / labels
        style.configure("TFrame",      background=bg)
        style.configure("TLabel",      background=bg, foreground=text)
        style.configure("TPanedwindow", background=bg, sashwidth=6, sashpad=2)
        style.configure("TLabelframe", background=bg, relief="flat")
        style.configure("TLabelframe.Label",
                         background=bg, foreground=primary,
                         font=("Segoe UI", 10, "bold"))

        # ---- buttons
        style.configure("TButton",
                         background=card,
                         foreground=text,
                         padding=(10, 5),
                         relief="flat",
                         borderwidth=1,
                         bordercolor=border)
        style.map("TButton",
                  background=[("active", border), ("pressed", border)],
                  relief=[("pressed", "flat")])

        style.configure("Accent.TButton",
                         font=("Segoe UI", 10, "bold"),
                         background=primary,
                         foreground="#ffffff",
                         padding=(12, 6),
                         relief="flat",
                         borderwidth=0)
        style.map("Accent.TButton",
                  background=[("active", primary_dark), ("pressed", primary_dark)])

        style.configure("Danger.TButton",
                         font=("Segoe UI", 10),
                         background=danger,
                         foreground="#ffffff",
                         padding=(10, 5),
                         relief="flat")
        style.map("Danger.TButton",
                  background=[("active", danger), ("pressed", danger)])

        # ---- notebook (tabs)
        style.configure("TNotebook",
                         background=bg,
                         borderwidth=0,
                         tabmargins=(0, 4, 0, 0))
        style.configure("TNotebook.Tab",
                         padding=(18, 9),
                         font=("Segoe UI", 10, "bold"),
                         background=card,
                         foreground=muted,
                         borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", bg)],
                  foreground=[("selected", primary)],
                  expand=[("selected", [0, 0, 0, 0])])

        # ---- treeview
        style.configure("Treeview",
                         rowheight=28,
                         font=("Segoe UI", 10),
                         background=card,
                         fieldbackground=card,
                         foreground=text,
                         borderwidth=0,
                         relief="flat")
        style.configure("Treeview.Heading",
                         font=("Segoe UI", 9, "bold"),
                         background=bg,
                         foreground=muted,
                         padding=(4, 6),
                         relief="flat",
                         borderwidth=0)
        style.map("Treeview",
                  background=[("selected", primary)],
                  foreground=[("selected", "#ffffff")])
        style.map("Treeview.Heading",
                  background=[("active", input_bg)])

        # ---- inputs
        style.configure("TCheckbutton",
                         background=bg, foreground=text)
        style.configure("TEntry",
                         fieldbackground=input_bg, foreground=text,
                         insertcolor=text, bordercolor=border,
                         lightcolor=border, darkcolor=border,
                         padding=4)
        style.configure("TCombobox",
                         fieldbackground=input_bg, foreground=text,
                         background=card, arrowcolor=text,
                         bordercolor=border,
                         padding=4)
        style.map("TCombobox",
                  fieldbackground=[("readonly", input_bg)],
                  foreground=[("readonly", text)],
                  selectbackground=[("readonly", primary)])
        style.configure("TSpinbox",
                         fieldbackground=input_bg, foreground=text,
                         background=card, arrowcolor=text,
                         bordercolor=border)

        # ---- scrollbars
        style.configure("Vertical.TScrollbar",
                         background=border, troughcolor=bg,
                         arrowcolor=muted, bordercolor=bg)
        style.configure("Horizontal.TScrollbar",
                         background=border, troughcolor=bg,
                         arrowcolor=muted, bordercolor=bg)

    def _build_menu(self):
        t = w.theme_colors()
        menubar = tk.Menu(self, bg=t["CARD"], fg=t["TEXT"],
                          activebackground=t["PRIMARY"], activeforeground="#ffffff",
                          borderwidth=0, relief="flat")

        filemenu = tk.Menu(menubar, tearoff=0,
                           bg=t["CARD"], fg=t["TEXT"],
                           activebackground=t["PRIMARY"], activeforeground="#ffffff")
        filemenu.add_command(label="Backup Database...",  command=self.backup_db)
        filemenu.add_command(label="Restore Database...", command=self.restore_db)
        filemenu.add_separator()
        filemenu.add_command(label="Open Data Folder...", command=self.open_data_folder)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.on_close)
        menubar.add_cascade(label="File", menu=filemenu)

        viewmenu = tk.Menu(menubar, tearoff=0,
                           bg=t["CARD"], fg=t["TEXT"],
                           activebackground=t["PRIMARY"], activeforeground="#ffffff")
        self.dark_mode_var = tk.BooleanVar(value=w.is_dark())
        viewmenu.add_checkbutton(
            label="Dark Mode", variable=self.dark_mode_var, command=self.toggle_dark_mode
        )
        menubar.add_cascade(label="View", menu=viewmenu)

        helpmenu = tk.Menu(menubar, tearoff=0,
                           bg=t["CARD"], fg=t["TEXT"],
                           activebackground=t["PRIMARY"], activeforeground="#ffffff")
        helpmenu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=helpmenu)
        self.config(menu=menubar)

    def _build_tabs(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(6, 10))

        from tabs_dashboard  import DashboardTab
        from tabs_properties import PropertiesTab
        from tabs_tenants    import TenantsTab
        from tabs_rent       import RentTab
        from tabs_reports    import ReportsTab
        from tabs_expenses   import ExpensesTab

        def _add_tab(TabClass, label):
            """Wrap every tab in a ScrollableFrame so that on a short
            window / small screen its content can be scrolled to instead
            of getting silently clipped and left unreachable. The real
            tab instance (with its .refresh(), etc.) is still what gets
            stored on `self` and used everywhere else in the app - only
            the notebook page itself is the scrollable container."""
            container = w.ScrollableFrame(self.notebook)
            tab = TabClass(container.body, self)
            tab.pack(fill="both", expand=True)
            # Let notebook-level code (on_tab_changed) that looks up the
            # selected page and calls .refresh() on it keep working.
            container.refresh = tab.refresh
            # The notebook now holds `container`, not `tab`, as its page.
            # Code elsewhere (e.g. "jump to Rent tab" from Dashboard) that
            # needs to call notebook.select(...) on a tab must select the
            # page via this reference instead of the tab object itself.
            tab.notebook_page = container
            self.notebook.add(container, text=label)
            return tab

        self.dashboard_tab  = _add_tab(DashboardTab,  "  Dashboard  ")
        self.properties_tab = _add_tab(PropertiesTab, "  Properties & Units  ")
        self.tenants_tab    = _add_tab(TenantsTab,    "  Tenants  ")
        self.rent_tab       = _add_tab(RentTab,       "  Rent Tracking  ")
        self.expenses_tab   = _add_tab(ExpensesTab,   "  Expenses  ")
        self.reports_tab    = _add_tab(ReportsTab,    "  Reports  ")

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # Route mouse-wheel scrolling to whichever tab's ScrollableFrame
        # is currently selected, no matter which widget inside it the
        # pointer happens to be over. Only needs to be set up once - the
        # lookup always resolves against whatever tab is selected *now*.
        w.bind_mousewheel_routing(self, self._current_scrollable)

    def _current_scrollable(self):
        try:
            page = self.notebook.nametowidget(self.notebook.select())
        except Exception:
            return None
        return page if isinstance(page, w.ScrollableFrame) else None

    def _rebuild_tabs(self, keep_selection=True):
        """Tear down and recreate the notebook and every tab. Used after
        a theme change so every widget picks up the new colors."""
        current_index = 0
        if keep_selection and hasattr(self, "notebook"):
            try:
                current_index = self.notebook.index(self.notebook.select())
            except Exception:
                current_index = 0
        if hasattr(self, "notebook"):
            self.notebook.destroy()
        self._build_tabs()
        try:
            self.notebook.select(current_index)
        except Exception:
            pass

    # ------------------------------------------------------------ theme
    def toggle_dark_mode(self):
        dark = self.dark_mode_var.get()
        w.set_mode("dark" if dark else "light")
        self.settings["dark_mode"] = dark
        self.db.save_settings(self.settings)
        self._setup_style()
        self._build_menu()
        self._rebuild_tabs()

    def open_data_folder(self):
        path = self.db.data_dir
        try:
            if os.name == "nt":
                os.startfile(path)
            elif os.uname().sysname == "Darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        except Exception as e:
            messagebox.showinfo(
                "Data folder",
                f"Your data is stored here:\n{path}\n\n(Couldn't open it automatically: {e})",
            )

    # ------------------------------------------------------------ cross-tab refresh
    def on_tab_changed(self, event=None):
        tab = self.notebook.nametowidget(self.notebook.select())
        if hasattr(tab, "refresh"):
            tab.refresh()

    def refresh_all(self):
        for tab in (self.dashboard_tab, self.properties_tab, self.tenants_tab,
                    self.rent_tab, self.expenses_tab, self.reports_tab):
            if hasattr(tab, "refresh"):
                tab.refresh()

    # ------------------------------------------------------------ menu actions
    def backup_db(self):
        path = filedialog.asksaveasfilename(
            title="Save backup as",
            defaultextension=".db",
            initialfile=f"tenant_manager_backup_{datetime.date.today().isoformat()}.db",
            filetypes=[("SQLite Database", "*.db"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            self.db.backup_to(path)
            messagebox.showinfo("Backup complete", f"Backup saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Backup failed", str(e))

    def restore_db(self):
        if not messagebox.askyesno(
            "Restore database",
            "This will replace ALL current data with the backup file's data.\n"
            "This cannot be undone. Continue?",
        ):
            return
        path = filedialog.askopenfilename(
            title="Select backup file",
            filetypes=[("SQLite Database", "*.db"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            self.db.restore_from(path)
            self.refresh_all()
            messagebox.showinfo("Restore complete", "Database restored successfully.")
        except Exception as e:
            messagebox.showerror("Restore failed", str(e))

    def show_about(self):
        messagebox.showinfo(
            "About",
            f"{APP_TITLE}\n\n"
            "Track properties, units, tenants and rent payments month "
            "by month, all stored locally in:\n"
            f"{self.db.path}\n\n"
            "Every change is also auto-saved to a plain, human-readable "
            "backup file in the same folder:\n"
            f"{self.db.export_path}\n\n"
            "Features:\n"
            "• Per-unit Rent History — set different rent amounts for\n"
            "  different date ranges (Properties & Units tab).\n"
            "• Rent records automatically use the correct amount for each\n"
            "  month when generated.\n"
            "• Tenant rent is always derived from the unit — no duplicate\n"
            "  entry needed.\n\n"
            "That whole folder travels with the app — copy the app's "
            "folder to a new PC and your data comes with it.",
        )

    def on_close(self):
        try:
            self.db.conn.commit()
        except Exception:
            pass
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
