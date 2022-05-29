install-vm:
	$(MAKE) -C qubes_tutorial_vm

install-dom0:
	install -m 664 -D README.md $(DESTDIR)/usr/lib/qubes/tutorial/README.md
	install -d $(DESTDIR)/usr/share/qubes/tutorial/
	cp -r qubes_tutorial/included_tutorials $(DESTDIR)/usr/share/qubes/tutorial/

clean:
	rm -rf pkgs