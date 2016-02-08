function fish_prompt
	set -g RETVAL $status
    prompt_status
    prompt_virtual_env
    prompt_user
    prompt_dir
    available hg
    and prompt_hg
    available git
    and prompt_git
    available svn
    and prompt_svn
    prompt_finish
    if set -q VIRTUAL_ENV
        echo -n -s (set_color -b blue white) "(" (basename "$VIRTUAL_ENV") ")" (set_color normal) " "
    end
end
