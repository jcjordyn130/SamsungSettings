import sys
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
import argparse
import pydbus

class MyApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        # Create a Builder
        builder = Gtk.Builder()
        builder.add_from_file("main.ui")

        # Grab D-Bus instance to the daemon
        bus = pydbus.SystemBus()
        try:
            self.proxy = bus.get("org.jordynsblog.SamsungSettingsDaemon", "/org/jordynsblog/SamsungSettingsDaemon")
        except gi.repository.GLib.GError:
            print(f"[ERROR] Failed to obtain a handle to the daemon on D-Bus... is it running???")
            daemonNotFoundDialog = builder.get_object("daemonNotFoundError")
            daemonNotFoundDialog.connect("response", lambda dialog, response: exit(1))
            daemonNotFoundDialog.set_application(self)
            daemonNotFoundDialog.present()
            return

        # Connect Setting widgets to their proper handlers and sync with the
        # settings file.
        self.usbChgButton = builder.get_object("usbChgButton")
        self.usbChgButton.connect("state-set", self.handleUSBCharging)
        self.usbChgButton.set_state(self.proxy.usbCharging)

        self.performanceMode = builder.get_object("box")
        self.performanceMode.connect("notify::selected", self.handlePerformanceMode)
        self.performanceMode.set_selected(self.proxy.perfMode)

        self.kbdBacklight = builder.get_object("but")
        self.kbdBacklight.connect("value-changed", self.handleKeyboardBacklight)
        self.kbdBacklight.set_value(self.proxy.kbdBacklight)

        self.batterySaver = builder.get_object("batterySaverSwitch")
        self.batterySaver.connect("state-set", self.handleBatterySaver)
        self.batterySaver.set_state(self.proxy.batterySaver)

        self.startOnLidOpen = builder.get_object("startOnLidOpenSwitch")
        self.startOnLidOpen.connect("state-set", self.handleStartOnLidOpen)
        self.startOnLidOpen.set_state(self.proxy.startOnLidOpen)

        # Obtain and show the main window
        self.win = builder.get_object("mainWindow")
        self.win.set_application(self)  # Application will close once it no longer has active windows attached to it

        # Check for module and show warning dialog if it doesn't exist before presenting the primary window.
        if not self.proxy.moduleLoaded:
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
        self.proxy.kbdBacklight = val
        self.proxy.Save()

    def handlePerformanceMode(self, obj, pspec):
        perfmodes = ["Silent", "Quiet", "Optimized", "High performance"] # NOTE: These are used for logging only
        selected = obj.get_selected()
        print(f"Changing performance mode to: {perfmodes[selected]}")
        self.proxy.perfMode = selected
        self.proxy.Save()

    def handleUSBCharging(self, switch, state):
        if state:
            print("[DEBUG] Turning USB Charging on!")
        else:
            print("[DEBUG] Turning USB Charging off!")

        self.proxy.usbCharging = state
        self.proxy.Save()

        # True stops other signals from emitting
        return False

    def handleBatterySaver(self, switch, state):
        if state:
            print(f"[DEBUG] Turning Battery Saver on!")
        else:
            print(f"[DEBUG] Turning Battery Saver off!")

        self.proxy.batterySaver = state
        self.proxy.Save()

        return False

    def handleStartOnLidOpen(self, switch, state):
        if state:
            print(f"[DEBUG] Turning Start On Lid Open on!")
        else:
            print(f"[DEBUG] Turning Start On Lid Open off!")

        self.proxy.startOnLidOpen = state
        self.proxy.Save()

        return False

parser = argparse.ArgumentParser(prog = "SamsungSettings", description = "A clone of Samsung Settings for Linux using the samsung-galaxybook kernel module.")
parser.add_argument("-r", "--restore", action = "store_true", help = "Restores saved settings on module reload or a reboot.")
parser.add_argument("-k", "--inckey", action = "store_true" , help = "Increments the keyboard backlight and wraps back around at 100 percent.")
args = parser.parse_args()

if args.restore:
    # Restore
    print(f"[DEBUG] [Main] Restoring settings then exiting!")
    bus = pydbus.SystemBus()
    proxy = bus.get("org.jordynsblog.SamsungSettingsDaemon", "/org/jordynsblog/SamsungSettingsDaemon")
    if not proxy.moduleLoaded:
        print(f"[ERROR] [Main] Cannot restore settings as samsung-galaxybook is not loaded or /sys/bus/platform/devices/samsung-galaxybook is otherwise missing!")
        raise SystemExit(1)
    proxy.Restore()
    raise SystemExit(0)
elif args.inckey:
    bus = pydbus.SystemBus()
    proxy = bus.get("org.jordynsblog.SamsungSettingsDaemon", "/org/jordynsblog/SamsungSettingsDaemon")

    if proxy.kbdBacklight == 3:
        proxy.kbdBacklight = 0
    else:
        proxy.kbdBacklight = proxy.kbdBacklight + 1

    proxy.Save()
else:
    # run GTK
    app = MyApp(application_id="org.jordynsblog.SamsungSettings")
    app.run(sys.argv)
