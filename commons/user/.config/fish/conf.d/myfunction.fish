function rm_fisherman
    if test -d ~/.config/fisherman
        rm -rf ~/.config/fisherman
    end

    if test -d ~/.cache/fisherman
        rm -rf ~/.cache/fisherman
    end

    if test -d ~/.local/share/fisherman
        rm -rf ~/.local/share/fisherman
    end
end

# Reinstall fisherman
# curl -Lo ~/.config/fish/functions/fisher.fish --create-dirs git.io/fisherman
