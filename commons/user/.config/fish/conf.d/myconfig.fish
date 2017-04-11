# Misc
set --global --export LANG fr_FR.UTF-8
set --local  HOSTNAME (hostname)

# Vars
set --global --export PRIVATE ~/private/projects
set --global --export TABMO_PROJECTS ~/work/projects
set --global --export GOPATH ~/private/projects/go 
set --global --export GOBIN ~/local/bin 
set --global --export  PATH $PATH /usr/sbin /usr/local/bin ~/local/bin $TABMO_PROJECTS/tabmo-tools

# Virtualenv
# Install with pip2 install virtualfish
eval (python2 -m virtualfish auto_activation compat_aliases)

# Start X at login
if status --is-login
  if test -z "$DISPLAY" -a $XDG_VTNR = 1
    exec startx -- -keeptty > ~/.xlog
  end
end
