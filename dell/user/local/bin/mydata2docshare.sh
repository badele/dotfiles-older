#!/usr/bin/env bash

if [ -d ~/.mytourbook ]; then
    # Backup
    DSTDIR=/home/badele/docshare/documents/Fammily/Bruno/backup
    echo "Backup mytourbook"
    cd ~
    tar -cvzf mytourbook.tgz ~/.mytourbook

    # Copy to git-annex repository
    cd $DSTDIR
    git annex unlock mytourbook.tgz
    cp ~/mytourbook.tgz $DSTDIR
    git annex add $DSTDIR/mytourbook.tgz
fi
