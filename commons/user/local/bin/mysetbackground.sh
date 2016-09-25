#!/bin/bash

COUNTERNAME='/tmp/mybackground_counter'
BG_FOLDER=~/.i3/pictures/

resetCounter()
{
    rm "$COUNTERNAME"
}


setMinCounter()
{
    newcounter=0
    test -e "$COUNTERNAME" || echo "$newcounter" > "$COUNTERNAME"

}

setMaxCounter()
{
    newcounter=$(ls $BG_FOLDER/* | wc -l)
    test -e "$COUNTERNAME" || echo "$newcounter" > "$COUNTERNAME"
}


addCounter()
{
    value=$1
    oldcounter=$(cat $COUNTERNAME)
    newcounter=$(expr $oldcounter + $value)
    echo $newcounter > $COUNTERNAME
}

showSelectedImage()
{
    echo "## $newcounter ##"
    BG_FILENAME=$(ls $BG_FOLDER/* | head -n$newcounter  | tail -n 1)
    feh --bg-scale $BG_FILENAME
}

showRandomImage()
{
    feh --randomize  --bg-scale $BG_FOLDER/*
}

case $1 in
        "next")
            setMinCounter
            addCounter 1
            showSelectedImage
            ;;

        "prev")
            setMaxCounter
            addCounter -1
            showSelectedImage
            ;;

        "top")
            resetCounter
            setMaxCounter
            showSelectedImage
            ;;

        "bottom")
            resetCounter
            setMinCounter
            addCounter 1
            showSelectedImage
            ;;

        "rand")
            showRandomImage
            ;;
    esac