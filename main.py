import sys
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
import argparse
import backend

class MyApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect("activate", self.on_activate)
        self.settings = backend.Settings()
    
        try:
            self.settings.Load()
        except FileNotFoundError:
            # We don't care
            print(f"[DEBUG] [MyApp]: Settings file not found...")

    def on_activate(self, app):
        # Create a Builder
        builder = Gtk.Builder()
        builder.add_from_file("main.ui")

        # Connect Setting widgets to their proper handlers and sync with the
        # settings file.
        self.usbChgButton = builder.get_object("usbChgButton")
        self.usbChgButton.connect("state-set", self.handleUSBCharging)
        self.usbChgButton.set_state(self.settings.getUSBCharging())

        self.performanceMode = builder.get_object("box")
        self.performanceMode.connect("notify::selected", self.handlePerformanceMode)
        self.performanceMode.set_selected(self.settings.getPerfMode())

        self.kbdBacklight = builder.get_object("but")
        self.kbdBacklight.connect("value-changed", self.handleKeyboardBacklight)
        self.kbdBacklight.set_value(self.settings.getKeyboardBacklight())

        # Obtain and show the main window
        self.win = builder.get_object("mainWindow")
        self.win.set_application(self)  # Application will close once it no longer has active windows attached to it

        # Check for module and show warning dialog if it doesn't exist before presenting the primary window.
        if not self.settings.IsModuleLoaded():
            print("[WARNING] samsung-galaxybook kernel module is not loaded... settings will NOT take effect!")
            print("See https://github.com/joshuagrisham/samsung-galaxybook-extras on how to install it.")
            kmodNotFoundDialog = builder.get_object("kmodNotFoundError")
            kmodNotFoundDialog.connect("response", self.handleKmodNotFoundDialog)
            kmodNotFoundDialog.set_application(self)
            kmodNotFoundDialog.present()
            return

        self.win.present()

    # This is not a static method as this function needs a reference to the original main window
    # to function correctly.
    def handleKmodNotFoundDialog(self, dialog, response):
        self.win.present()

    def handleKeyboardBacklight(self, object):
        val = object.get_value()
        self.settings.setKeyboardBacklight(val)
        self.settings.Save()

    def handlePerformanceMode(self, obj, pspec):
        perfmodes = ["Silent", "Quiet", "Optimized", "High performance"] # NOTE: These are used for logging only
        selected = obj.get_selected()
        print(f"Changing performance mode to: {perfmodes[selected]}")
        self.settings.setPerfMode(selected)
        self.settings.Save()

    def handleUSBCharging(self, switch, state):
        if state:
            print("[DEBUG] Turning USB Charging on!")
        else:
            print("[DEBUG] Turning USB Charging off!")

        self.settings.setUSBCharging(state)
        self.settings.Save()

        # True stops other signals from emitting
        return False

parser = argparse.ArgumentParser(prog = "SamsungSettings", description = "A clone of Samsung Settings for Linux using the samsung-galaxybook kernel module.")
parser.add_argument("-r", "--restore", action = "store_true", help = "Restores saved settings on module reload or a reboot.")
parser.add_argument("-k", "--inckey", action = "store_true" , help = "Increments the keyboard backlight and wraps back around at 100 percent.")
args = parser.parse_args()

if args.restore:
    # Restore
    print(f"[DEBUG] [Main] Restoring settings then exiting!")
    settings = backend.Settings()
    if not settings.IsModuleLoaded():
        print(f"[ERROR] [Main] Cannot restore settings as samsung-galaxybook is not loaded or /sys/bus/platform/devices/samsung-galaxybook is otherwise missing!")
        raise SystemExit(1)
    settings.Restore()
    raise SystemExit(0)
elif args.inckey:
    settings = backend.Settings()
    try:
        settings.Load()
    except FileNotFoundError:
        # We don't care
        print(f"[DEBUG] [MyApp]: Settings file not found...")


    if settings.getKeyboardBacklight() == 3.0:
        settings.setKeyboardBacklight(0.0)
    else:
        settings.setKeyboardBacklight(settings.getKeyboardBacklight() + 1)

    settings.Save()
else:
    # run GTK
    app = MyApp(application_id="org.jordynsblog.SamsungSettings")
    app.run(sys.argv)
