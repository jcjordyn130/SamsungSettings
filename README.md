# SamsungSettings
A Samsung Settings clone for Linux using the [samsung-galaxybook kernel module](https://github.com/joshuagrisham/samsung-galaxybook-extras).

![Application UI](screenshot.png?raw=true)

It is really basic, but more features will be added as the underlying kernel module adds them.

### How to Use
For most use cases, just running the script is enough to invoke it.

The one exception is that unless the permissions on the `/sys/bus/platform/samsung-galaxybook` files are changed
then only running this application as root will have any effect.

There are a few command line switches that can be given though.

```
$ python3 main.py --help
usage: SamsungSettings [-h] [-r] [-k]

A clone of Samsung Settings for Linux using the samsung-galaxybook kernel module.

options:
  -h, --help     show this help message and exit
  -r, --restore  Restores saved settings on module reload or a reboot.
  -k, --inckey   Increments the keyboard backlight and wraps back around at 100 percent.
```

The `-r`/`--restore` parameter is used to restore saved settings on module reload or reboot
because the Samsung Galaxy Book series of machines don't keep the perferences in between reboots.

Additionally, the `-k`/`--inckey` parameter is used to increment the keyboard backlight and wrap it back around at 100%.

This is because, unlike most machines, the Samsung Galaxy Book series only has a backlight key on the keyboard
that functions like that. It does NOT have keyboard brightness up and down keys as certain desktop environments assume.

#### Dependencies
The only external Python dependencies this script has is pydbus. 
Otherwise, this script just depends on Python, it's stdlib, GTK4+ and libadwaita 1+.