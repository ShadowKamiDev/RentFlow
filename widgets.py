"""
widgets.py - small reusable UI helpers shared across tabs, plus the
light/dark theme system.

Theme system
------------
Colors used to be plain module-level constants (COLOR_BG, COLOR_CARD,
...). They are now resolved dynamically through module __getattr__ so
that every other file can keep writing `w.COLOR_BG`, `w.STATUS_COLORS`
etc. exactly as before, but the value returned depends on whichever
theme (light/dark) is currently active. Call `w.set_mode("dark")` /
`w.set_mode("light")` (or `w.toggle_mode()`) to switch themes; the
app rebuilds its widgets afterwards so the new colors take effect.
"""

import tkinter as tk
from tkinter import ttk
import datetime
import sys

# ---------------------------------------------------------------- themes
THEMES = {
    "light": {
        # Base surfaces
        "BG":           "#eef2f7",      # cool blue-grey page background
        "CARD":         "#ffffff",      # white card surface
        "INPUT_BG":     "#f8fafc",      # very slightly off-white input
        "BORDER":       "#d1dae8",      # visible but soft border

        # Brand / accent
        "PRIMARY":      "#1d4e89",      # deep navy blue (matches icon)
        "PRIMARY_DARK": "#16396a",      # darker navy for hover
        "PRIMARY_LIGHT":"#dde9f6",      # tint for hover states

        # Semantic colours
        "SUCCESS":      "#1a7a4a",      # dark green
        "WARNING":      "#92620a",      # amber-brown
        "DANGER":       "#b52a2a",      # deep red

        # Text
        "TEXT":         "#1a202c",      # near-black
        "MUTED":        "#64748b",      # blue-grey muted text

        # Status row tinting (subtle — readable against white card)
        "STATUS_COLORS": {
            "Paid":    "#d4edda",       # mint green
            "Partial": "#fff3cd",       # warm yellow
            "Unpaid":  "#fde8e8",       # light rose
            "Overdue": "#f5c2c2",       # stronger rose-red
        },
        "OCCUPANCY_COLORS": {
            "vacant":  "#fff3cd",       # amber tint
            "occupied":"#d4edda",       # green tint
        },
    },

    "dark": {
        # Base surfaces — true dark, blue-tinted
        "BG":           "#0d1117",      # near-black, GitHub-dark inspired
        "CARD":         "#161b22",      # dark navy card
        "INPUT_BG":     "#1c2128",      # slightly lighter input
        "BORDER":       "#30363d",      # subtle grey border

        # Brand / accent — brighter to pop on dark bg
        "PRIMARY":      "#58a6ff",      # bright cornflower blue
        "PRIMARY_DARK": "#388bfd",      # slightly deeper for hover
        "PRIMARY_LIGHT":"#1c2e4a",      # dark-tinted for backgrounds

        # Semantic colours — vivid enough for dark bg
        "SUCCESS":      "#3fb950",      # GitHub green
        "WARNING":      "#d29922",      # golden yellow
        "DANGER":       "#f85149",      # bright red

        # Text
        "TEXT":         "#e6edf3",      # almost white
        "MUTED":        "#8b949e",      # cool grey

        # Status row tinting — dark but distinguishable
        "STATUS_COLORS": {
            "Paid":    "#0d2a1a",       # deep emerald
            "Partial": "#2d2005",       # dark amber
            "Unpaid":  "#2d0f0f",       # dark crimson
            "Overdue": "#3d0f0f",       # deeper crimson
        },
        "OCCUPANCY_COLORS": {
            "vacant":  "#2d2005",       # dark amber
            "occupied":"#0d2a1a",       # deep emerald
        },
    },
}

_state = {"mode": "light"}


def _theme():
    return THEMES[_state["mode"]]


def is_dark():
    return _state["mode"] == "dark"


def set_mode(mode):
    """mode: 'light' or 'dark'"""
    if mode not in THEMES:
        mode = "light"
    _state["mode"] = mode


def toggle_mode():
    set_mode("light" if is_dark() else "dark")
    return _state["mode"]


def theme_colors():
    """Return a plain dict snapshot of the currently active theme."""
    return dict(_theme())


def __getattr__(name):
    # Lets other modules keep using w.COLOR_BG, w.STATUS_COLORS, etc.
    # This only fires for `widgets.NAME` access from *outside* this
    # module (PEP 562), so it never interferes with the internal
    # helpers below, which use _theme() directly.
    theme = _theme()
    if name.startswith("COLOR_"):
        key = name[len("COLOR_"):]
        if key in theme:
            return theme[key]
    if name in ("STATUS_COLORS", "OCCUPANCY_COLORS"):
        return theme[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def entry_colors(include_cursor=True):
    """Kwargs to spread into raw tk widgets (Text, Listbox, etc.) so
    they follow the current theme instead of tkinter's default
    white-on-black look. Pass include_cursor=False for widgets like
    Listbox that don't support insertbackground."""
    t = _theme()
    colors = dict(
        bg=t["INPUT_BG"],
        fg=t["TEXT"],
        selectbackground=t["PRIMARY"],
        selectforeground="#ffffff",
        highlightthickness=1,
        highlightbackground=t["BORDER"],
        highlightcolor=t["PRIMARY"],
        relief="flat",
    )
    if include_cursor:
        colors["insertbackground"] = t["TEXT"]
    return colors


def apply_entry_colors(widget):
    """Reconfigure an already-created Text/Listbox widget in place."""
    try:
        widget.configure(**entry_colors())
    except Exception:
        pass


def scrolled_tree(parent, columns, **tree_kwargs):
    """Create a ttk.Treeview paired with a vertical scrollbar, inside a
    small holder frame, and return (holder, tree).

    Configure headings/columns on the returned `tree` exactly as you
    would for a plain Treeview, then pack (or grid) `holder` wherever
    you would previously have packed the tree itself - e.g.:

        holder, self.tree = w.scrolled_tree(parent, columns, height=10)
        for c in columns:
            self.tree.heading(c, text=...)
            self.tree.column(c, width=...)
        holder.pack(fill="both", expand=True, pady=6)

    Why a holder frame instead of just packing a scrollbar next to the
    tree directly in `parent`: the tree needs side="left"/fill="both"
    to sit flush against the scrollbar, but if `parent` has other
    widgets packed *after* it (e.g. a row of buttons below the table),
    Tk does not reserve height for them the way stacking two side="top"
    widgets does - a left/right pair only shrinks the cavity's *width*,
    not its height, so anything packed below ends up overlapping and
    hidden behind the table. Wrapping tree+scrollbar in their own
    holder means that overlap only happens *inside* the holder (which
    has nothing else in it), and the holder itself behaves as a single
    block for whatever is packed around it, exactly like the plain
    tree did before.
    """
    holder = ttk.Frame(parent)
    tree = ttk.Treeview(holder, columns=columns, show="headings", **tree_kwargs)
    scrollbar = ttk.Scrollbar(holder, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    return holder, tree


# ---------------------------------------------------------------- dates
def month_name(period):
    """'2026-06' -> 'June 2026'"""
    try:
        dt = datetime.datetime.strptime(period, "%Y-%m")
        return dt.strftime("%B %Y")
    except Exception:
        return period


def current_period():
    return datetime.date.today().strftime("%Y-%m")


def shift_period(period, delta_months):
    y, m = (int(x) for x in period.split("-"))
    idx = y * 12 + (m - 1) + delta_months
    y, m = idx // 12, idx % 12 + 1
    return f"{y:04d}-{m:02d}"


def compute_status(amount_due, amount_paid, due_date):
    if amount_due <= 0:
        return "Paid"
    if amount_paid >= amount_due:
        return "Paid"
    today = datetime.date.today().isoformat()
    if due_date and due_date < today:
        return "Overdue"
    if amount_paid > 0:
        return "Partial"
    return "Unpaid"


def fmt_money(value):
    try:
        return f"₹{value:,.2f}"
    except Exception:
        return str(value)


# ---------------------------------------------------------------- widgets
class ScrollableFrame(ttk.Frame):
    """A frame with a vertical scrollbar, content goes in self.body.

    Used to wrap tabs/panels so that on a short window or small screen
    nothing gets silently clipped off the bottom - the user can always
    scroll to reach it. The scrollbar only appears when content actually
    overflows, and mouse-wheel scrolling is routed in from the app level
    (see bind_mousewheel_routing) rather than scoped with per-widget
    Enter/Leave - Enter/Leave breaks the instant the pointer is over any
    child widget (a button, label, treeview...) instead of bare canvas
    background, which is most of the visible area, making the wheel feel
    like it randomly stops working.
    """

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.canvas = canvas = tk.Canvas(self, bg=_theme()["BG"], highlightthickness=0)
        self.scrollbar = scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.body = ttk.Frame(canvas)
        self._scrollbar_visible = False

        self._window = canvas.create_window((0, 0), window=self.body, anchor="nw")

        self.body.bind("<Configure>", lambda e: self._sync())
        # Keep the inner body exactly as wide as the visible canvas, so
        # fill="x"/"both" children stretch to the full width of the tab
        # instead of shrinking to their minimum requested width.
        canvas.bind("<Configure>", self._on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        # Scrollbar is added/removed from view in _sync() as needed,
        # rather than always being packed.

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self._window, width=event.width)
        self._sync()

    def _sync(self):
        """Show the scrollbar only when content taller than the visible
        area actually exists, and keep the scroll region accurate."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.body.update_idletasks()
        content_h = self.body.winfo_reqheight()
        visible_h = self.canvas.winfo_height()
        needs_scroll = content_h > visible_h
        if needs_scroll and not self._scrollbar_visible:
            self.scrollbar.pack(side="right", fill="y")
            self._scrollbar_visible = True
        elif not needs_scroll and self._scrollbar_visible:
            self.scrollbar.pack_forget()
            self._scrollbar_visible = False
            self.canvas.yview_moveto(0)

    def scroll(self, units):
        """Scroll by `units` lines (positive = down). No-op if nothing
        to scroll - called by the app-level mouse-wheel router."""
        if self._scrollbar_visible:
            self.canvas.yview_scroll(units, "units")


def bind_mousewheel_routing(root, get_active_scrollable):
    """Call once, at the app level. Routes mouse-wheel scrolling to
    whichever ScrollableFrame `get_active_scrollable()` currently returns
    (e.g. the tab that's presently selected) no matter which widget the
    pointer happens to be over. This avoids the classic Tk problem where
    scoping a wheel binding to one widget via Enter/Leave stops working
    as soon as the pointer is over any child widget inside it.

    Handles both Windows/macOS (<MouseWheel>) and Linux/X11
    (<Button-4>/<Button-5>, which is what X11 sends instead)."""

    def _on_wheel(event):
        target = get_active_scrollable()
        if target is None:
            return
        num = getattr(event, "num", None)
        if num == 4:
            target.scroll(-1)
        elif num == 5:
            target.scroll(1)
        else:
            delta = event.delta
            if sys.platform == "darwin":
                target.scroll(int(-1 * delta))
            else:
                target.scroll(int(-1 * (delta / 120)))

    root.bind_all("<MouseWheel>", _on_wheel)
    root.bind_all("<Button-4>", _on_wheel)
    root.bind_all("<Button-5>", _on_wheel)


class LabeledEntry(ttk.Frame):
    """A label above an entry, with a convenient .get()/.set()."""

    def __init__(self, parent, label, width=24, **kwargs):
        super().__init__(parent)
        ttk.Label(self, text=label, foreground=_theme()["MUTED"]).pack(anchor="w")
        self.var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.var, width=width, **kwargs)
        self.entry.pack(anchor="w", fill="x")

    def get(self):
        return self.var.get()

    def set(self, value):
        self.var.set("" if value is None else value)


class FlowFrame(ttk.Frame):
    """A toolbar-style frame that lays its children out left-to-right and
    wraps onto a new row whenever they would overflow the available
    width, instead of letting them run off the edge of the window like
    a plain pack(side="left") row does. Makes button bars adapt to
    narrow / small screens so every option stays visible and reachable.

    Usage:
        bar = w.FlowFrame(self)
        bar.pack(fill="x", padx=16, pady=(16, 8))
        bar.add(ttk.Button(bar, text="Do thing", command=...))
        bar.add(ttk.Button(bar, text="Do other thing", command=...), pad_left=16)

    Widgets must be created with this frame as their parent, then
    registered with .add(widget) instead of calling .pack()/.grid() on
    them directly - FlowFrame manages their position itself.
    """

    def __init__(self, parent, hgap=6, vgap=6, **kwargs):
        super().__init__(parent, **kwargs)
        self.hgap = hgap
        self.vgap = vgap
        self._items = []  # list of (widget, extra_left_gap)
        self._last_width = None
        # Bind both Configure (resize) and Map (becomes visible, e.g. a
        # notebook tab being selected for the first time) - relying on
        # Configure alone isn't enough because a frame sitting on a
        # not-yet-selected notebook tab reports width 0/1 and never
        # fires Configure until it's actually shown.
        self.bind("<Configure>", self._on_event)
        self.bind("<Map>", self._on_event)

    def add(self, widget, pad_left=0):
        self._items.append((widget, pad_left))
        if self.winfo_ismapped():
            self._relayout()
        return widget

    def clear(self):
        for widget, _ in self._items:
            try:
                widget.destroy()
            except Exception:
                pass
        self._items = []

    def _on_event(self, event=None):
        width = self.winfo_width()
        # width<=1 means this frame isn't actually visible yet (e.g. an
        # unselected notebook tab) - nothing to lay out, and importantly
        # we must NOT reschedule ourselves here, or we'd spin forever
        # waiting for a size that will only arrive once the tab is shown.
        if width <= 1 or width == self._last_width:
            return
        self._last_width = width
        self._relayout()

    def _relayout(self):
        width = self.winfo_width()
        if width <= 1:
            return
        x = y = 0
        row_height = 0
        for widget, pad_left in self._items:
            widget.update_idletasks()
            req_w = widget.winfo_reqwidth()
            req_h = widget.winfo_reqheight()
            gap = self.hgap + pad_left
            if x > 0 and x + gap + req_w > width:
                x = 0
                y += row_height + self.vgap
                row_height = 0
                gap = pad_left
            elif x > 0:
                x += gap
            widget.place(x=x, y=y, width=req_w, height=req_h)
            x += req_w
            row_height = max(row_height, req_h)
        new_height = y + row_height
        if str(self.cget("height")) != str(new_height):
            self.configure(height=new_height)


def card(parent, **kwargs):
    t = _theme()
    f = tk.Frame(parent, bg=t["CARD"], highlightbackground=t["BORDER"],
                 highlightthickness=1, **kwargs)
    return f


def stat_card(parent, title, value, color=None):
    t = _theme()
    if color is None:
        color = t["PRIMARY"]
    f = card(parent)
    # Accent stripe — packed first as a non-Label child so it won't be
    # picked up by _set_card()'s isinstance(c, tk.Label) filter.
    tk.Frame(f, bg=color, width=4).pack(side="left", fill="y")
    # Title and value labels are direct children of f (labels[0] and labels[1])
    # so that _set_card() in dashboard/reports can still find and update them.
    tk.Label(f, text=title, bg=t["CARD"], fg=t["MUTED"],
             font=("Segoe UI", 9),
             padx=12).pack(anchor="w", pady=(10, 2))
    tk.Label(f, text=value, bg=t["CARD"], fg=color,
             font=("Segoe UI", 20, "bold"),
             padx=12).pack(anchor="w", pady=(0, 10))
    return f
