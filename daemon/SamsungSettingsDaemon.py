#!/bin/env python3
import pydbus
import pathlib
import json
from gi.repository import GLib, Gio
import sys

try:
    import sdnotify
except ModuleNotFoundError:
    print(f"[NOTE] Disabling systemd-notify support as sdnotify is not installed!")

class Settings():
    """ The Settings() class is a high level class that implements the actual logic in SamsungSettings.

    Specifically, it handles the actual loading/saving of settings from/to a JSON file
    for restoration on boot and it handles the actual setting of the settings using
    either the /sys filesystem entries or other daemons via D-Bus (mainly the gsd-power daemon as of now).

    It's only really used in the Daemon() class below for logical seperation of functionality
    and to avoid a monster class.

    """

    # Directory containing path to kernel tunables for samsung-galaxybook module
    # NB: these won't work unless we're running as root or the user configured
    # their permissions correctly.
    sysfiles = {"base": pathlib.Path("/sys/bus/platform/devices/samsung-galaxybook")}
    sysfiles.update({
        "usbchg": sysfiles["base"] / "usb_charging",
        "perfmode": sysfiles["base"] / "performance_mode",
        "kbdbacklight": pathlib.Path("/sys/class/leds/samsung-galaxybook::kbd_backlight/brightness"),
        "batterySaver": sysfiles["base"] / "battery_saver",
        "startOnLidOpen": sysfiles["base"] / "start_on_lid_open"
    })

    settings = {
        "usbCharging": False,
        "perfMode": 0,
        "kbdBacklight": 0,
        "batterySaver": False,
        "startOnLidOpen": False
    }

    def IsModuleLoaded(self):
        return self.sysfiles["base"].exists()

    def Save(self, file = "settings.json"):
        print(f"[DEBUG] [Settings]: Saving settings to {file}")
        with open(file, "w") as fileh:
            json.dump(self.settings, fileh)

    def Load(self, file = "settings.json"):
        print(f"[DEBUG] [Settings]: Loading settings from {file}")
        with open(file, "r") as fileh:
            settings = json.load(fileh)

            # The settings dictonary is being loaded in this weird way so values that exist in the default dictonary
            # aren't removed from loading an older settings file.
            for key in settings:
                self.settings.update({key: settings[key]})

    def Restore(self, file = "settings.json"):
        print(f"[DEBUG] [Settings]: Restoring settings from {file}")
        self.Load(file)
        self.setUSBCharging(self.settings["usbCharging"])
        self.setPerfMode(self.settings["perfMode"])
        self.setKeyboardBacklight(self.settings["kbdBacklight"])
        self.setBatterySaver(self.settings["batterySaver"])
        self.setStartOnLidOpen(self.settings["startOnLidOpen"])

    def getUSBCharging(self):
        return self.settings["usbCharging"]

    def getPerfMode(self):
        return self.settings["perfMode"]

    def getKeyboardBacklight(self):
        return self.settings["kbdBacklight"]

    def getBatterySaver(self):
        return self.settings["batterySaver"]

    def getStartOnLidOpen(self):
        return self.settings["startOnLidOpen"]

    def setUSBCharging(self, val):
        print(f"[DEBUG] [Settings]: Setting USB Charging to {val}!")
        try:
            self.sysfiles["usbchg"].write_text(f"{val}")
        except FileNotFoundError:
            print(f"[ERROR] {self.sysfiles['usbchg']} was not found! is samsung-galaxybook loaded???")

        # I put this here instead of in the above exception block so that the user
        # can change settings if they don't have the module loaded and it'll
        # still be saved to the settings file.
        self.settings["usbCharging"] = val
    
    def setPerfMode(self, val):
        print(f"[DEBUG] [Settings]: Setting Performance Mode to {val}!")
        if val not in [0, 1, 2, 3]:
            raise ValueError("Performance Mode value cannot be less than 0 or more than 3!")
            
        try:
            self.sysfiles["perfmode"].write_text(f"{val}")
        except FileNotFoundError:
            print(f"[ERROR] {self.sysfiles['perfmode']} was not found! is samsung-galaxybook loaded???")

        self.settings["perfMode"] = val

    def setKeyboardBacklight(self, val):
        print(f"[DEBUG] [Settings]: Setting keyboard backlight to {val}!")
        if val < 0 or val > 3:
            raise ValueError("Backlight value must be in between 0-3!")

        def method_1(self, val):
            try:
                bus = pydbus.SessionBus()
                powermethod = bus.get("org.gnome.SettingsDaemon.Power")
                keyboardmethod = powermethod.__getitem__("org.gnome.SettingsDaemon.Power.Keyboard") # TODO: don't use __getitem__
                keyboardmethod.Brightness = val
            finally:
                self.settings["kbdBacklight"] = val

        def method_2(self, val):
            try:
                self.sysfiles["kbdbacklight"].write_text(f"{val}")
            finally:
                self.settings["kbdBacklight"] = val

        try:
            print(f"[DEBUG] [Settings]: Using Method 1 -- gsd-power over D-Bus")
            method_1(self, val)
            return
        except GLib.GError:
            print(f"[ERROR] [Settings]: GError exception occured during keyboard backlight changing... either gsd-power is not running or a connection to the D-Bus session bus cannot be obtained!")

        try:
            print(f"[DEBUG] [Settings]: Using Method 2 -- /sys")
            method_2(self, val)
            return
        except FileNotFoundError:
            print(f"[ERROR] {self.sysfiles['kbdbacklight']} was not found! is samsung-galaxybook loaded???")

    def setBatterySaver(self, val):
        if val not in [0, 1, False, True]:
            raise ValueError("Battery Saver setting must be an integer or a boolean!")

        # Convert value to integer for writing to /sys.
        # This will either keep the value if it's already an integer
        # or convert a boolean to an integer representation.
        val = int(val)
        print(f"[DEBUG] [Settings]: Setting battery saver to {val}!")
        try:
            self.sysfiles["batterySaver"].write_text(f"{val}")
        except FileNotFoundError:
            print(f"[ERROR] {self.sysfiles['batterySaver']} was not found! is samsung-galaxybook loaded???")

        self.settings["batterySaver"] = val

    def setStartOnLidOpen(self, val):
        print(f"[DEBUG] [Settings]: Setting Start on Lid Open to {val}!")
        if val not in [0, 1, False, True]:
            raise ValueError("Start on Lid Open setting must be an integer or a boolean!")

        # Convert value to integer for writing to /sys.
        # This will either keep the value if it's already an integer
        # or convert a boolean to an integer representation.
        val = int(val)
        try:
            self.sysfiles["startOnLidOpen"].write_text(f"{val}")
        except FileNotFoundError:
            print(f"[ERROR] {self.sysfiles['startOnLidOpen']} was not found! is samsung-galaxybook loaded???")

        self.settings["startOnLidOpen"] = val

class Daemon():
    """ The Daemon() class is responsible for the high level funcionality of the SamsungSettings daemon.

    It lets the Settings() class handle the loading and saving of settings while implementing the interface
    that other applications use over D-Bus.

    It also handles syncing the /sys filesystem entries to the saved settings file when other applications
    modify them, as gsd-power does when the keyboard backlight is changed from within GNOME.

    And for systemd users, it also pings the service manager using the sdnotify protocol once 
    everything is ready and every second or so for watchdog support.
    """

    # I'm putting the D-Bus definitions in here as it's one less file I have to install.
    dbus = """
        <node>
            <interface name="org.jordynsblog.SamsungSettingsDaemon">
            <method name="Save">
                <arg type="s" name="response" direction="out"/>
            </method>
            <method name="Load">
                <arg type="s" name="response" direction="out"/>
            </method>
            <method name="Restore">
                <arg type="s" name="response" direction="out"/>
            </method>
            <property name="moduleLoaded" type="b" access="read">
                <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
            </property>
            <property name="usbCharging" type="b" access="readwrite">
                <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
            </property>
            <property name="perfMode" type="n" access="readwrite">
                <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
            </property>
            <property name="kbdBacklight" type="n" access="readwrite">
                <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
            </property>
            <property name="batterySaver" type="b" access="readwrite">
                <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
            </property>
            <property name="startOnLidOpen" type="b" access="readwrite">
                <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
            </property>
            </interface>
        </node>"""

    PropertiesChanged = pydbus.generic.signal()

    def __init__(self):
        self.settings = Settings()
        try:
            self.settings.Restore()
        except FileNotFoundError:
            print(f"[DEBUG] settings.json not found!")

        self.ignoresyschanges = False

    def handle_file_change(self, monitor, file1, file2, evt_type):
        if evt_type != Gio.FileMonitorEvent.CHANGED:
            print("handle_file_change called with unneeded event... skipping!")
            return

        # File2 is only used during a move which cannot happen on /sys filesystems.
        path = file1.get_path()

        if self.ignoresyschanges:
            print(f"Ignoring changed file {path} as ignoresyschanges is True!")
            return

        if path == self.settings.sysfiles["usbchg"]:
            newval = int(self.settings.sysfiles["usbchg"].read_text())
            self.usbCharging = newval
            self.settings.Save()
        elif path == self.settings.sysfiles["perfmode"]:
            newval = int(self.settings.sysfiles["perfmode"].read_text())
            self.perfMode = newval
            self.settings.Save()
        elif path == self.settings.sysfiles["kbdbacklight"]:
            newval = int(self.settings.sysfiles["kbdbacklight"].read_text())
            self.kbdBacklight = newval
            self.settings.Save()
        elif path == self.settings.sysfiles["batterySaver"]:
            newval = int(self.settings.sysfiles["batterySaver"].read_text())
            self.batterySaver = newval
            self.settings.Save()
        elif path == self.settings.sysfiles["startOnLidOpen"]:
            newval = int(self.settings.sysfiles["startOnLidOpen"].read_text())
            self.startOnLidOpen = newval
            self.settings.Save()
        else:
            print(f"Unknown file changed: {path}!")

    @staticmethod
    def ping_systemd(user_data):
        #print(f"[INFO]: Pinging systemd watchdog!")
        notifier = sdnotify.SystemdNotifier()
        notifier.notify("WATCHDOG=1")
        return True

    def Save(self):
        self.settings.Save()
        return "true"

    def Load(self):
        self.settings.Load()
        return "true"

    def Restore(self):
        self.settings.Restore()
        return "true"

    @property
    def moduleLoaded(self):
        return self.settings.IsModuleLoaded()

    @property
    def usbCharging(self):
        return self.settings.getUSBCharging()

    @usbCharging.setter
    def usbCharging(self, value):
        self.ignoresyschanges = True
        self.settings.setUSBCharging(value)
        #self.ignoresyschanges = False
        self.PropertiesChanged("org.jordynsblog.SamsungSettingsDaemon", {"usbCharging": value}, [])
        
    @property
    def perfMode(self):
        return self.settings.getPerfMode()

    @perfMode.setter
    def perfMode(self, value):
        self.ignoresyschanges = True
        self.settings.setPerfMode(value)
        self.ignoresyschanges = False
        self.PropertiesChanged("org.jordynsblog.SamsungSettingsDaemon", {"perfMode": value}, [])

    @property
    def kbdBacklight(self):
        return self.settings.getKeyboardBacklight()

    @kbdBacklight.setter
    def kbdBacklight(self, value):
        self.ignoresyschanges = True
        self.settings.setKeyboardBacklight(value)
        self.ignoresyschanges = False
        self.PropertiesChanged("org.jordynsblog.SamsungSettingsDaemon", {"kbdBacklight": value}, [])

    @property
    def batterySaver(self):
        return self.settings.getBatterySaver()

    @batterySaver.setter
    def batterySaver(self, value):
        self.ignoresyschanges = True
        self.settings.setBatterySaver(value)
        self.ignoresyschanges = False
        self.PropertiesChanged("org.jordynsblog.SamsungSettingsDaemon", {"batterySaver": value}, [])

    @property
    def startOnLidOpen(self):
        return self.settings.getStartOnLidOpen()

    @startOnLidOpen.setter
    def startOnLidOpen(self, value):
        self.ignoresyschanges = True
        self.settings.setStartOnLidOpen(value)
        self.ignoresyschanges = False
        self.PropertiesChanged("org.jordynsblog.SamsungSettingsDaemon", {"startOnLidOpen": value}, [])

# Base code
import os 
print(f"SamsungSettingsDaemon starting up! PID: {os.getpid()}")

# Check for module
if not Settings.sysfiles["base"].exists():
    print(f"[ERROR]: samsung-galaxybook module is not loaded!")
    raise SystemExit(1)

# Setup D-Bus
bus = pydbus.SystemBus()
obj = Daemon()
bus.publish("org.jordynsblog.SamsungSettingsDaemon", obj)

# Setup /sys watch
leddir = Gio.File.new_for_path("/sys/class/leds/samsung-galaxybook::kbd_backlight")
basedir = Gio.File.new_for_path("/sys/bus/platform/devices/samsung-galaxybook")
ledmonitor = leddir.monitor_directory(Gio.FileMonitorFlags(0), None)
ledmonitor.connect("changed", obj.handle_file_change)
basemonitor = leddir.monitor_directory(Gio.FileMonitorFlags(0), None)
basemonitor.connect("changed", obj.handle_file_change)

# Notify systemd users
if "sdnotify" in sys.modules:
    print(f"[INFO]: Sending ready notification and PID to systemd!")
    notifier = sdnotify.SystemdNotifier()
    notifier.notify(f"MAINPID={os.getpid()}")
    notifier.notify("READY=1")

    # Setup systemd watchdog to ping every second
    GLib.timeout_add(1000, obj.ping_systemd, None)

# Main loop
# I figure since Glib's mainloop is needed for pydbus I might as well use it for
# file watching too.
loop = GLib.MainLoop()
loop.run()
