# Load configuration ressources
xrdb ~/.Xresources

# Active compiz alternative
compton -cCG -b  --vsync opengl

# Active numlock and disable the touchpad
numlockx &
synclient touchpadoff=1

# Launch the i3 window manager
exec dbus-launch i3
