.PHONY: install uninstall

LOCALPREFIX := /usr/local
PREFIX := /usr

install:
	install -Dm 0755 SamsungSettings.py $(PREFIX)/bin
	install -Dm 0644 SamsungSettings.ui $(PREFIX)/share/SamsungSettings/SamsungSettings.ui

uninstall:
	rm -v $(PREFIX)/bin/SamsungSettings.py
	rm -v $(PREFIX)/share/SamsungSettings/SamsungSettings.ui