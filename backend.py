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
        "kbdbacklight": pathlib.Path("/sys/class/leds/samsung-galaxybook::kbd_backlight/brightness")
    })

    settings = {
        "usbCharging": False,
        "perfMode": 0,
        "kbdBacklight": 0.0
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
            self.settings = json.load(fileh)

    def Restore(self, file = "settings.json"):
        print(f"[DEBUG] [Settings]: Restoring settings from {file}")
        self.Load(file)
        self.setUSBCharging(self.settings["usbCharging"])
        self.setPerfMode(self.settings["perfMode"])
        self.setKeyboardBacklight(self.settings["kbdBacklight"])

    def getUSBCharging(self):
        return self.settings["usbCharging"]

    def getPerfMode(self):
        return self.settings["perfMode"]

    def getKeyboardBacklight(self):
        return self.settings["kbdBacklight"]

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