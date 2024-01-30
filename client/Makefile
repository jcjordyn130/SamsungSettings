.PHONY: install uninstall

LOCALPREFIX := /usr/local
PREFIX := /usr

install:
	install -m 0755 SamsungSettingsDaemon.py $(LOCALPREFIX)/bin
	install -m 0644 SamsungSettingsDaemon.conf $(PREFIX)/share/dbus-1/system.d
	install -m 0644 SamsungSettings.service $(PREFIX)/lib/systemd/system/

uninstall:
	rm -v $(LOCALPREFIX)/bin/SamsungSettingsDaemon.py
	rm -v $(PREFIX)/share/dbus-1/system.d/SamsungSettingsDaemon.conf
	rm -v $(PREFIX)/lib/systemd/system/SamsungSettings.service