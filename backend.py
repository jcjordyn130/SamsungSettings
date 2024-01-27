import json
import pathlib
import gi
import pydbus

class Settings():
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
        except gi.repository.GLib.GError:
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