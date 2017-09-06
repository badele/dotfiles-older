
```
                ██████╗  ██████╗ ████████╗███████╗██╗██╗     ███████╗███████╗
                ██╔══██╗██╔═══██╗╚══██╔══╝██╔════╝██║██║     ██╔════╝██╔════╝
                ██║  ██║██║   ██║   ██║   █████╗  ██║██║     █████╗  ███████╗
                ██║  ██║██║   ██║   ██║   ██╔══╝  ██║██║     ██╔══╝  ╚════██║
                ██████╔╝╚██████╔╝   ██║   ██║     ██║███████╗███████╗███████║
                ╚═════╝  ╚═════╝    ╚═╝   ╚═╝     ╚═╝╚══════╝╚══════╝╚══════╝
                
                                   For Archlinux distribution
```

### Installation

```bash
git clone git@github.com:badele/dotfiles.git
cd dotfiles
./setup.sh

# Select environment with
mystow.sh apply commons
mystow.sh apply dell
```

This dotfiles use

 * Dotfiles manager
  * stow
  
 * I3 window manager
  * i3-gaps-git ( The I3 next generation )
  * i3blocks ( The i3 status bar next generation )
  * compton ( compiz manager )
  * feh ( background manager )
  * dunst ( lightweigth notification )
  * rofi ( dmenu alternative )
  * xedgewarp (mouse in multi-screen manager )
  * maim ( Screenshot capture )
  * numlockx (active numlock at boot)

* XFCE
  * libmtp (MPT Photos thunar support)   
 
* Fish shell
  * powerline font (patched powerline font)
  * fisherman (fish plugins)
  * virtualfish (virtualenv plugin)

Boot process

 * autologin console with systemd call getty@tty1.service, 
 * call .config/fish/config.fish
 * launch i3
