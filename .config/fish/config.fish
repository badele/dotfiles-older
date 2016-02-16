set fisher_home ~/.local/share/fisherman
set fisher_config ~/.config/fisherman
source $fisher_home/config.fish

# Misc
set --global --export LANG fr_FR.UTF-8
set --local  HOSTNAME (hostname)

# Vars
set --global --export PRIVATE ~/private/projects
set --global --export WORK ~/work/projects

set --global --export  PATH $PATH /usr/sbin /usr/local/bin ~/local/bin

# Regenerate symlink for ~/local/bin
find ~/local/bin -type l -delete
set files (ls ~/local/$HOSTNAME/bin)
for file in $files; 
	ln -s ~/local/$HOSTNAME/bin/$file ~/local/bin/$file
end

# Virtualenv
# Install with pip2 install virtualfish
eval (python2 -m virtualfish auto_activation compat_aliases) 

# Start X at login
if status --is-login
  if test -z "$DISPLAY" -a $XDG_VTNR = 1
    exec startx -- -keeptty > ~/.xlog
  end
end
