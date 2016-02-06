# Path to Oh My Fish install.
set -gx OMF_PATH "/home/badele/.local/share/omf"

# Customize Oh My Fish configuration path.
#set -gx OMF_CONFIG "/home/badele/.config/omf"

# Load oh-my-fish configuration.
source $OMF_PATH/init.fish

# Misc
set --erase fish_greeting
set --global --export LANG fr_FR.UTF-8

# Start X at login
if status --is-login
  if test -z "$DISPLAY" -a $XDG_VTNR = 1
    exec startxfce4 -- -keeptty > ~/.xlog
  end
end
