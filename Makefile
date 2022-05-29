install-vm:
	$(MAKE) -C qubes_tutorial_vm

install-dom0:
	install -m 664 -D README.md $(DESTDIR)/usr/lib/qubes/tutorial/README.md

clean:
	rm -rf pkgs