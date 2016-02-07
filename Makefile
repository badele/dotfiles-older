all:
	@echo "Please select target"

requirements:
	@yaourt -S maim xdotool slop;

powerlinefont:
	@rm -rf /tmp/fonts; \
	cd /tmp; \
	git clone https://github.com/powerline/fonts.git; \
	cd fonts; \
	./install.sh

.PHONY: requirements powerlinefont
