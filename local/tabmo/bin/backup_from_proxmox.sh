#!/bin/bash

if [ "$TABMO_PROXMOX_BACKUP" != "" ]; then
	rsync -avr --progress $TABMO_PROXMOX_BACKUP /mnt/tabmobackup/Backup/OVH/Proxmox/
fi

