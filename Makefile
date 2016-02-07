all:
	@echo "Please select target"

requirements:
	# I3
	@yaourt -S i3-gaps compton dunst rofi xedgewarp-git

	# Editors
	@yaourt -S nano-syntax-highlighting-git; \
	@yaourt -S geany geany-themes; \

	# Screenshot
	@yaourt -S maim xdotool slop;

powerlinefont:
	# Powerline fonts installation
	@rm -rf /tmp/fonts; \
	cd /tmp; \
	git clone https://github.com/powerline/fonts.git; \
	cd fonts; \
	./install.sh

.PHONY: requirements powerlinefont
