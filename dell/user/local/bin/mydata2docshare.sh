#!/usr/bin/env bash

if [ -d ~/.mytourbook ]; then
    # Backup
    DSTDIR=~/docshare/documents/Fammily/Bruno/backup
    echo "Backup mytourbook"
    cd ~
    tar -cvzf mytourbook.tgz ~/.mytourbook

    # Copy to git-annex repository
    cd $DSTDIR
    git annex unlock mytourbook.tgz
    cp ~/mytourbook.tgz $DSTDIR
    git annex add $DSTDIR/mytourbook.tgz
fi

if [ -d ~/Downloads/tomtom_mysport ]; then
    # Backup
    DSTDIR=~/docshare/documents/Fammily/Bruno/backup
    echo "Backup tomtom mysport"
    cd ~/Downloads
    tar -cvzf tomtom_mysport.tgz ~/Downloads/tomtom_mysport

    # Copy to git-annex repository
    cd $DSTDIR
    git annex unlock tomtom_mysport.tgz
    cp ~/Downloads/tomtom_mysport.tgz $DSTDIR
    git annex add $DSTDIR/tomtom_mysport.tgz
fi
