# SamsungSettings
A Samsung Settings clone for Linux using the [samsung-galaxybook kernel module](https://github.com/joshuagrisham/samsung-galaxybook-extras).

![Application UI](screenshot.png?raw=true)

It is really basic, but more features will be added as the underlying kernel module adds them.


### Dependencies
All it depends on is Python3 and it's standard library, pydbus, Glib (and GTK for the GUIClient), and optionally sdnotify if you
want to use the sdnotify protocol.

So, for most systems, all that's needed is to install pydbus and optionally sdnotify.

In Red Hat and it's derivatives, this can be done using `sudo dnf install python3-pydbus python3-sdnotify`.

In Debian and it's derivatives, it can be done using `sudo apt install python3-pydbus python3-sdnotify`

Otherwise, you can use the requirements.txt file given by using `sudo pip3 install -r requirements.txt`. However, this is *NOT* recommended as this installs global python packages using Pip which can cause issues with other applications on the system.

### How to Use
#### Daemon
There is a daemon that must be installed before the GUI client can be used.

It can be installed via the Makefile using `make install`, then either managed by your init system of choice 
or managed using the systemd unit file included.

If you're using systemd, all that's needed is `systemctl enable --now SamsungSettings.service`.

As certain settings (mainly Performance Mode) must be reset everytime the system is booted, the daemon
restores all settings upon startup assuming that the settings.json file is present and readable.

It will also monitor /sys for changes and keep it's internal settings database updated so that
settings can be changed outside of this application (through GNOME, though the shell, whereever).

#### Client
The client uses D-Bus to communicate with the daemon so the daemon and it's dependencies must be installed and running
otherwise the client will exit.

Using the client is as easy as running `GUIClient/main.py`.

There are a few command line switches that can be given though.

```
$ python3 main.py --help
usage: SamsungSettings [-h] [-r] [-k] [-u UIFILE]

A clone of Samsung Settings for Linux using the samsung-galaxybook kernel module.

options:
  -h, --help            show this help message and exit
  -r, --restore         Restores saved settings on module reload or a reboot.
  -k, --inckey          Increments the keyboard backlight and wraps back around at 100 percent.
  -u UIFILE, --uifile UIFILE
                        Sets the location for the UI file.
```

The `-r`/`--restore` parameter is used to restore saved settings on module reload or reboot
because the Samsung Galaxy Book series of machines don't keep the perferences in between reboots.

This is technically redundant as the daemon does this automatically upon loading, but the argument
can be used to force it if need be.

Additionally, the `-k`/`--inckey` parameter is used to increment the keyboard backlight and wrap it back around at 100%.

This is because, unlike most machines, the Samsung Galaxy Book series only has a backlight key on the keyboard
that that adjusts the brightness and wraps around. It does NOT have keyboard brightness up and down keys as certain desktop environments assume.

The `-u`/`--uifile` parameter is used to pass a custom location of the .ui file to `Gtk.Builder()`. Normally, this wouldn't be needed, but I haven't quite figured out where to put that file that's clean... well, other than sticking it in SamsungSettings.py as a string.