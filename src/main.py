# main.py - land.rob.Nectar

import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, Gtk

from .store import Store
from .window import NectarWindow

APP_ID = "land.rob.Nectar"
VERSION = "0.1.0"


class NectarApplication(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID,
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self._store = None

        about = Gio.SimpleAction.new("about", None)
        about.connect("activate", self._about)
        self.add_action(about)

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda *_: self.quit())
        self.add_action(quit_action)
        self.set_accels_for_action("app.quit", ["<primary>q"])

    def do_activate(self):
        win = self.props.active_window
        if not win:
            if self._store is None:
                self._store = Store()
            win = NectarWindow(self, self._store)
        win.present()

    def _about(self, *_):
        dlg = Adw.AboutDialog(
            application_name="Nectar",
            application_icon=APP_ID,
            developer_name="Rob",
            version=VERSION,
            website="https://rob.land",
            license_type=Gtk.License.GPL_3_0,
        )
        dlg.present(self.props.active_window)


def main():
    app = NectarApplication()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
