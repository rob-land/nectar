# window.py - the game
#
# One vertical column inside a clamp: rank + progress, the word being
# typed, the 2-3-2 honeycomb, controls, and the found-words flow. Sized
# for a phone first; on a desktop it just sits centered. Letters are
# tappable AND typeable (EventControllerKey), because the desktop half
# of the audience has a keyboard.

import datetime
import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from . import game
from .game import Puzzle

CSS = """
.nectar-letter {
  font-size: 22px;
  font-weight: 800;
  min-width: 64px;
  min-height: 64px;
}
.nectar-center {
  background: #f5c211;
  color: #3d3846;
}
.nectar-word {
  font-size: 26px;
  font-weight: 800;
  letter-spacing: 2px;
}
.nectar-found {
  padding: 2px 10px;
  border-radius: 999px;
  background: alpha(@accent_bg_color, 0.15);
}
.nectar-pangram {
  background: alpha(#f5c211, 0.45);
  font-weight: 700;
}
"""


class NectarWindow(Adw.ApplicationWindow):
    def __init__(self, app, store):
        super().__init__(application=app, title="Nectar")
        self.set_default_size(400, 700)
        self._store = store
        self._puzzle = None
        self._found = []
        self._score = 0
        self._current = ""

        provider = Gtk.CssProvider()
        provider.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self._toasts = Adw.ToastOverlay()
        tv = Adw.ToolbarView()
        header = Adw.HeaderBar()
        tv.add_top_bar(header)

        menu = Gio.Menu()
        menu.append("How to Play", "win.help")
        menu.append("About Nectar", "app.about")
        header.pack_end(Gtk.MenuButton(icon_name="open-menu-symbolic",
                                       menu_model=menu))
        help_action = Gio.SimpleAction.new("help", None)
        help_action.connect("activate", self._help)
        self.add_action(help_action)

        self._spinner_page = Adw.StatusPage(title="Mixing today's nectar…")
        spinner = Gtk.Spinner(spinning=True, width_request=32,
                              height_request=32, halign=Gtk.Align.CENTER)
        self._spinner_page.set_child(spinner)

        self._stack = Gtk.Stack()
        self._stack.add_named(self._spinner_page, "loading")
        self._stack.add_named(self._build_board(), "board")
        tv.set_content(self._stack)
        self._toasts.set_child(tv)
        self.set_content(self._toasts)

        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self._on_key)
        self.add_controller(keys)

        self._load_today()

    # -- board construction ----------------------------------------------

    def _build_board(self):
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14,
                      margin_top=12, margin_bottom=18,
                      margin_start=12, margin_end=12)

        self._rank_label = Gtk.Label(xalign=0, css_classes=["heading"])
        self._progress = Gtk.LevelBar(min_value=0, max_value=1)
        rank_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        rank_box.append(self._rank_label)
        rank_box.append(self._progress)
        col.append(rank_box)

        self._word_label = Gtk.Label(label=" ", css_classes=["nectar-word"],
                                     halign=Gtk.Align.CENTER)
        col.append(self._word_label)

        self._letter_buttons = []
        hive = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                       halign=Gtk.Align.CENTER)
        for count in (2, 3, 2):
            row = Gtk.Box(spacing=8, halign=Gtk.Align.CENTER)
            for _ in range(count):
                btn = Gtk.Button(css_classes=["circular", "nectar-letter"])
                btn.connect("clicked", self._letter_clicked)
                row.append(btn)
                self._letter_buttons.append(btn)
            hive.append(row)
        col.append(hive)

        controls = Gtk.Box(spacing=8, halign=Gtk.Align.CENTER)
        for label, cb in (("Delete", self._delete),
                          ("Shuffle", self._shuffle),
                          ("Enter", self._submit)):
            b = Gtk.Button(label=label, css_classes=["pill"])
            b.connect("clicked", cb)
            controls.append(b)
        controls.get_last_child().add_css_class("suggested-action")
        col.append(controls)

        self._found_flow = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE,
                                       max_children_per_line=4,
                                       row_spacing=6, column_spacing=6,
                                       homogeneous=False,
                                       valign=Gtk.Align.START)
        found_scroll = Gtk.ScrolledWindow(
            child=self._found_flow, vexpand=True,
            hscrollbar_policy=Gtk.PolicyType.NEVER)
        col.append(found_scroll)

        return Adw.Clamp(child=col, maximum_size=480)

    # -- puzzle lifecycle -------------------------------------------------

    def _load_today(self):
        date_str = datetime.date.today().isoformat()
        cached = self._store.cached_puzzle(date_str)
        if cached is not None:
            letters, answers = cached
            self._set_puzzle(Puzzle(date_str, letters, answers))
            return
        self._stack.set_visible_child_name("loading")

        def gen():
            puzzle = game.generate(date_str)
            self._store.cache_puzzle(date_str, puzzle.letters,
                                     list(puzzle.answers))
            GLib.idle_add(self._set_puzzle, puzzle)

        threading.Thread(target=gen, daemon=True,
                         name="nectar-gen").start()

    def _set_puzzle(self, puzzle):
        self._puzzle = puzzle
        self._current = ""
        self._found = self._store.found_words(puzzle.date)
        self._found = [w for w in self._found if w in puzzle.answers]
        self._score = sum(game.word_score(w, puzzle.letterset)
                          for w in self._found)

        self._apply_letters(puzzle.letters)
        self._found_flow.remove_all()
        for w in sorted(self._found):
            self._add_chip(w)
        self._update_progress()
        self._update_word()
        self._stack.set_visible_child_name("board")
        return GLib.SOURCE_REMOVE

    def _apply_letters(self, letters):
        # letters[0] is the center; board order is 2-3-2 with the center
        # in the middle of the middle row (index 3).
        outer = list(letters[1:])
        order = outer[:3] + [letters[0]] + outer[3:]
        for btn, letter in zip(self._letter_buttons, order):
            btn.set_label(letter.upper())
            btn._letter = letter
            btn.remove_css_class("nectar-center")
        self._letter_buttons[3].add_css_class("nectar-center")

    # -- input ------------------------------------------------------------

    def _letter_clicked(self, btn):
        self._current += btn._letter
        self._update_word()

    def _on_key(self, _c, keyval, _code, _state):
        ch = chr(Gdk.keyval_to_unicode(keyval) or 0).lower()
        if self._puzzle and ch.isalpha():
            self._current += ch
            self._update_word()
            return True
        if keyval == Gdk.KEY_BackSpace:
            self._delete(None)
            return True
        if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            self._submit(None)
            return True
        return False

    def _delete(self, _btn):
        self._current = self._current[:-1]
        self._update_word()

    def _shuffle(self, _btn):
        if self._puzzle is None:
            return
        import random
        outer = list(self._puzzle.letters[1:])
        random.shuffle(outer)
        self._apply_letters(self._puzzle.center + "".join(outer))

    def _submit(self, _btn):
        if self._puzzle is None or not self._current:
            return
        word = self._current
        self._current = ""
        self._update_word()

        if word in self._found:
            self._toast("Already found")
            return
        ok, result = self._puzzle.check(word)
        if not ok:
            self._toast(result)
            return

        self._found.append(word)
        self._store.add_found(self._puzzle.date, word)
        self._score += result
        self._add_chip(word)
        self._update_progress()

        if word in self._puzzle.pangrams:
            self._toast(f"Pangram! +{result}")
        elif self._score >= self._puzzle.max_score:
            self._toast("Queen Bee! Every word found.")
        else:
            self._toast(f"Nice! +{result}")

    # -- display ----------------------------------------------------------

    def _update_word(self):
        self._word_label.set_label(self._current.upper() or " ")

    def _add_chip(self, word):
        chip = Gtk.Label(label=word, css_classes=["nectar-found"])
        if self._puzzle and word in self._puzzle.pangrams:
            chip.add_css_class("nectar-pangram")
        self._found_flow.append(chip)

    def _update_progress(self):
        p = self._puzzle
        self._rank_label.set_label(
            f"{p.rank(self._score)} — {self._score} pts · "
            f"{len(self._found)}/{len(p.answers)} words"
        )
        self._progress.set_value(
            self._score / p.max_score if p.max_score else 0)

    def _toast(self, text):
        self._toasts.add_toast(Adw.Toast.new(text))

    def _help(self, *_):
        dlg = Adw.AlertDialog(
            heading="How to Play",
            body="Make words of four or more letters using the seven "
                 "letters in the hive. Every word must use the center "
                 "letter. Letters can repeat. A word that uses all seven "
                 "letters is a pangram and scores a bonus. Same puzzle "
                 "for everyone each day — come back tomorrow for a new "
                 "hive.",
        )
        dlg.add_response("ok", "Got It")
        dlg.present(self)
