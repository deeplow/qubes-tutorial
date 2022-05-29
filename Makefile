install-vm:
	$(MAKE) -C qubes_tutorial_vm

install-dom0:
	mkdir -p $(DESTDIR)/etc/qubes-rpc/
	cp qubes-rpc/tutorial.NextStep $(DESTDIR)/etc/qubes-rpc/tutorial.NextStep
	mkdir -p $(DESTDIR)/etc/qubes/policy.d/
	cp qubes-rpc-policy/80-tutorial.policy $(DESTDIR)/etc/qubes/policy.d/80-tutorial.policy

clean:
	rm -rf pkgs