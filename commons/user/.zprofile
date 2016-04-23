export PATH=~/local/$HOSTNAME/bin:~/local/bin:$PATH

[[ -z $DISPLAY && $XDG_VTNR -eq 1 ]] && exec startxfce4 > ~/.xlog
