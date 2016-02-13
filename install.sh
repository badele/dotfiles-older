#!/bin/bash

install_requirements() {
	# I3
	yaourt -S i3-gaps-git compton dunst rofi xedgewarp-git tty-clock numlockx

	# Editors
	yaourt -S nano-syntax-highlighting-git
	yaourt -S geany geany-themes

	# Screenshot
	yaourt -S maim xdotool slop

	# Fish
	install  fish
	chsh -s /usr/bin/fish

	# install fisherman
	sudo pip2 install virtualfish
	curl -sL install.fisherman.sh | fish
}

powerlinefont:(){
	# Powerline fonts installation
	rm -rf /tmp/fonts
	cd /tmp
	git clone https://github.com/powerline/fonts.git
	cd fonts
	./install.sh
}

if [ "$1" == "" ]; then
	echo "Please set action (requirements, powerlinefont)"
	exit 0
fi

if [ "$1" == "requirements" ]; then
	install_requirements
fi
