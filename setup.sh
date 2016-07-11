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

# Optional
# mytourbook_bin
install_requirements() {
    echo "- Install Requirements"
    # Dotfiles manager
    INSTALL="stow"

    # I3
    INSTALL="$INSTALL i3-gaps-git i3lock-wrapper compton dunst rofi xedgewarp-git tty-clock numlockx"
    
    #I3blocks
    INSTALL="$INSTALL i3blocks acpi bc lm_sensors playerctl sysstat"

    # XFCE
    INSTALL="$INSTALL libmtp"
    
    # Editors
    INSTALL="$INSTALL nano-syntax-highlighting-git"
    INSTALL="$INSTALL geany geany-themes"

    # Screenshot
    INSTALL="$INSTALL maim xdotool slop"
    
    # Misc
    INSTALL="$INSTALL galculator grc"

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

    # Install fisherman requirement
    if [ ! -d ~/.local/share/fisherman ]; then
        sudo pip2 install virtualfish
    fi
    #curl -Lo ~/.config/fish/functions/fisher.fish --create-dirs git.io/fisher
    #fisher oh-my-fish/theme-bobthefish grc ssh-term-helper gitignore tuvistavie/fish-ssh-agent
}

# Sync user computer specific files
configure_user_computer() {
    echo "- Install User computer configuration"
    if [ -f ~/.Xresources.def ]; then
        cpp -P ~/.Xresources.def ~/.Xresources
        xrdb ~/.Xresources
    fi

    # For dell computer
    if [ $HOSTNAME == "dell" ]; then
        ln -s ~/docshare/documents/Fammily/Bruno/mytourbook ~/.mytourbook
    fi
}

# Init commons stow
init_stow() {
    ./commons/user/local/bin/mystow.sh commons
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
configure_user_computer
init_stow
