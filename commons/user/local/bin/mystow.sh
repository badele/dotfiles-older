#!/bin/bash

PWD=$(pwd)


# Check if in the dotfiles folder
if [ ! -f "$PWD/README.md" ]; then
    echo "Please go to your root dotfiles folder"
    exit 0
else
    grep dotfiles "$PWD/README.md" > /dev/null
    if [ $? == 1 ]; then
        echo "Please go to your root dotfiles folder"
        exit 0
    fi
fi


# Execute stow
if [ $# -ge 1 ]; then
    NBARGS=$(($# - 1))
    OPTS=${@:1:$NBARGS}
    ENV=${*: -1}

    if [ -d "$PWD/$ENV/user" ]; then
        stow -d $PWD/$ENV -t ~ $OPTS user
    fi

    if [ -d "$PWD/$ENV/system" ]; then
        sudo stow -d $PWD/$ENV -t / $OPTS system
    fi
fi
