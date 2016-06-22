#!/bin/bash

# Create autologin (seem symbolical links by stow not working
rm -rf /'etc/systemd/system/getty@tty1.service.d'
mkdir -p '/etc/systemd/system/getty@tty1.service.d'
cp $PWD/fix/commons/system/etc/systemd/system/getty@tty1.service.d/autologin.conf '/etc/systemd/system/getty@tty1.service.d'