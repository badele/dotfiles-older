# SYNOPSIS
#   ssh [arguments]
#
# USAGE
#   ssh-term-helper overloads the 'ssh' command and changes the 
#   value of $TERM to a conservative setting present in most
#   termcap files. Any arguments are passed directly to the ssh
#   command.
#

function ssh -d "OpenSSH SSH client (remote login program) with a conservative $TERM value"
  switch $TERM
    case screen-256color
      set -lx TERM screen
      command ssh $argv
    case xterm-256color
      set -lx TERM xterm
      command ssh $argv
    case '*'
      command ssh $argv
  end
end
