#!/bin/bash

HOSTNAME=$(hostname)

needed_packages() {
    # Check package needed
    INSTALLED=$(yaourt -Q)
    TOINSTALL=""
    for  PACKAGE in $INSTALL; do
        ISINSTALLED=$(echo "$INSTALLED" | grep "/$PACKAGE")
        if [ $? -eq 1 ]; then
            TOINSTALL="$TOINSTALL $PACKAGE"
        fi
    done
    
    echo "$TOINSTALL"
}

install_requirements() {
    echo "- Install Requirements"
	# I3
	INSTALL="i3-gaps-git compton dunst rofi xedgewarp-git tty-clock numlockx"
    
    #I3blocks
    INSTALL="$INSTALL i3blocks acpi bc lm_sensors playerctl sysstat"

	# Editors
	INSTALL="$INSTALL nano-syntax-highlighting-git"
	INSTALL="$INSTALL geany geany-themes"

	# Screenshot
	INSTALL="$INSTALL maim xdotool slop"

    # Install needed packages
    NEEDED=$(needed_packages)
    if [  "$NEEDED" != "" ]; then
        yaourt -S $NEEDED
    fi

	# Fish
	INSTALL="fish"
    NEEDED=$(needed_packages)
    if [  "$NEEDED" != "" ]; then
        yaourt -S $NEEDED
        chsh -s /usr/bin/fish
    fi
	
    # install fisherman
    if [ ! -d ~/.local/share/fisherman ]; then
        sudo pip install virtualfish
        curl -sL install.fisherman.sh | fish
    fi
}

# Sync user computer specific files
sync_user_computer() {
    echo "- Install User computer configuration"
    cp ~/.asoundrc.$HOSTNAME ~/.asoundrc
}

# Sync user computer specific files
sync_system_computer() {
    echo "- Install System computer"
    sudo rsync -ar ~/system/ /
}

# For information, now is included in doftfiles-shell
powerlinefont:(){
	# Powerline fonts installation
	rm -rf /tmp/fonts
	cd /tmp
	git clone https://github.com/powerline/fonts.git
	cd fonts
	./install.sh
}

# Install
install_requirements
sync_user_computer
sync_system_computer
