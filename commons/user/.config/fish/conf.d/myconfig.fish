# Misc
set --global --export LANG fr_FR.UTF-8
set --local  HOSTNAME (hostname)

# Vars
set --global --export PRIVATE ~/private/projects
set --global --export TABMO_PROJECTS ~/work/projects

set --global --export  PATH $PATH /usr/sbin /usr/local/bin ~/local/bin $TABMO_PROJECTS/tabmo-tools

# Virtualenv
# Install with pip2 install virtualfish
eval (python2 -m virtualfish auto_activation compat_aliases)

# SSH Agent
# https://github.com/tuvistavie/fish-ssh-agent
# fisher tuvistavie/fish-ssh-agent
if test -z "$SSH_ENV"
    setenv SSH_ENV $HOME/.ssh/environment
end

if not __ssh_agent_is_started
    __ssh_agent_start
end


# Start X at login
if status --is-login
  if test -z "$DISPLAY" -a $XDG_VTNR = 1
    exec startx -- -keeptty > ~/.xlog
  end
end
