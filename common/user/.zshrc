# If not running interactively, do not do anything
[[ $- != *i* ]] && return
#[[ -z "$TMUX" ]] && exec tmux


if [ -f ~/docshare/scripts/private_vars.sh ]; then
  source ~/docshare/scripts/private_vars.sh
fi

# Conf
HOSTNAME=$(hostname)

# Regenerate symlink for ~/local/bin
find ~/local/bin -type l -delete
files=($(ls ~/local/$HOSTNAME/bin))
for file in $files; do
	ln -s ~/local/$HOSTNAME/bin/$file ~/local/bin/$file
done

# Path to your oh-my-zsh configuration.
ZSH=$HOME/.oh-my-zsh

# Set name of the theme to load.
# Look in ~/.oh-my-zsh/themes/
# Optionally, if you set this to "random", it'll load a random theme each
# time that oh-my-zsh is loaded.
ZSH_THEME="blinks"

export PRIVATE=~/private/projects
export TABMO_PROJECTS=~/work/projects
export GEM_HOME=$(ruby -e 'print Gem.user_dir')

# Example aliases
# alias zshconfig="mate ~/.zshrc"
# alias ohmyzsh="mate ~/.oh-my-zsh"
alias prj_fabrecipe="workon fabtools && cd ~/projects/fabrecipes/fabrecipes"
alias prj_blogjsl="workon pelican && cd ~/projects/blog.jesuislibre.org"
alias prj_badim="workon pelican && cd ~/projects/bruno.adele.im"
alias prj_cacause="workon cacause && cd ~/projects/cacause"
alias prj_jobcatcher="workon jobcatcher && cd ~/projects/JobCatcher"
alias prj_githubsum="workon githubsum && cd ~/projects/github-summary"
alias prj_serialkiller="workon serialkiller && cd ~/projects/serialkiller/serialkiller"
alias prj_pysdrscan="workon pysdrscan && cd ~/projects/pysdrscan/pysdrscan"
alias prj_sdrhunter="workon sdrhunter && cd ~/docshare_OLD/projects/SDRHunter/SDRHunter"
alias ssh_domotique="ssh root@192.168.253.58"
alias ssh_washroom="ssh pi@192.168.253.26"
alias ssh_tts="ssh root@192.168.253.34"
alias ssh_p03="ssh root@192.168.253.50"
alias ssh_video="ssh root@10.0.0.33"
alias ssh_p01="ssh root@p01.mon-vpn.com"
alias ssh_backup="ssh root@192.168.253.53"


# Set to this to use case-sensitive completion
# CASE_SENSITIVE="true"

# Comment this out to disable bi-weekly auto-update checks
# DISABLE_AUTO_UPDATE="true"

# Uncomment to change how many often would you like to wait before auto-updates occur? (in days)
# export UPDATE_ZSH_DAYS=13

# Uncomment following line if you want to disable colors in ls
# DISABLE_LS_COLORS="true"

# Uncomment following line if you want to disable autosetting terminal title.
# DISABLE_AUTO_TITLE="true"

# Uncomment following line if you want red dots to be displayed while waiting for completion
COMPLETION_WAITING_DOTS="true"

# Which plugins would you like to load? (plugins can be found in ~/.oh-my-zsh/plugins/*)
# Custom plugins may be added to ~/.oh-my-zsh/custom/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
#plugins=(git virtualenvwrapper cp docker python colored-man)
plugins=(python)

# # Virtualenv wrapper
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python2
export WORKON_HOME=~/.virtualenvs
export PROJECT_ROOT=$PROJECTS_PRIVATE
mkdir -p $WORKON_HOME
. virtualenvwrapper.sh

source $ZSH/oh-my-zsh.sh
unsetopt correct_all

# Customize to your needs...

if [ -d /opt/android-studio/bin ]; then
  export PATH=/opt/android-studio/bin:$PATH
fi

if [ -d $TABMO_PROJECTS/tabmo-tools ]; then
  export PATH=$TABMO_PROJECTS/tabmo-tools:$PATH
fi


PATH="$(ruby -e 'print Gem.user_dir')/bin:$PATH"

export SERIALKILLER_SETTINGS=/etc/sk_config.cfg
export EDITOR="nano"

. ~/.zshrc.private
