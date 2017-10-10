# This file belongs in $ELS/bin

# To facilitate debugging or verbosity of specific programs, this
# library supports setting defaults on a per-program basis using
# the following two files. See default_enable_verbose() and
# default_enable_debug() for more.

#HELP_Global: /etc/environment contents
#HELP_Global: ELS_DEFAULT_VERBOSE
ELS_DEFAULT_VERBOSE=$HOME/.ELS_DEFAULT_VERBOSE
#HELP_Global: ELS_DEFAULT_DEBUG
ELS_DEFAULT_DEBUG=$HOME/.ELS_DEFAULT_DEBUG

# This file provides functions for Elsevier scripts. It assumes
# the calling script is also using Google's shFlags module.
#HELP_Global export: UNAVAILABLE
export UNAVAILABLE="__unavailable__"
#HELP_Global export: UNDEFINED
export UNDEFINED="__undefined__"
#HELP_Global export: INVALID
export INVALID="__invalid__"
#HELP_Global export: NONEXISTENT
export NONEXISTENT="nonexistent" 
#HELP_Global export: TMPDIR
export TMPDIR=${TMPDIR:-/tmp}

#HELP_Global: PROGRAM
export PROGRAM="${0##-}"
#HELP_Global: BASE
export BASE=$(basename "$PROGRAM")
#HELP_Global: PWD
export PWD=$(pwd); export PWD
#HELP_Global: COMMAND
export COMMAND=""
#HELP_Global: LOG
LOG="eval _log \${BASH_SOURCE} \${LINENO}"

# Global variables to facilitate use of Github API
#HELP_Global: ELSORGURL
export ELSORGURL="https://api.github.com/orgs/elsevierPTG"
#HELP_Global: ELSREPOURL
export ELSREPOURL="$ELSORGURL/repos"
#HELP_Global: INDREPOURL (for individual repos)
export INDREPOURL="https://api.github.com/repos/elsevierPTG"
#HELP_Global: GIT_USER_API
#HELP After placing this file in $ELS/bin, replace this var
#HELP     with '-u $username:$gitapitoken'
export GIT_USER_API=""

# Enable more detailed debugging output.
# http://wiki.bash-hackers.org/scripting/debuggingtips
# Using embedded tab at the end of the string to make output more visually aligned
# and readable, e.g.:
# +(/opt/dims/bin/dims.ansible-playbook:427): main():     [[ 1 -eq 0 ]]
# +(/opt/dims/bin/dims.ansible-playbook:430): main():     is_fqdn --tags
# ++(/opt/dims/bin/dims_functions.sh:328): is_fqdn():     parse_fqdn --tags
# ++(/opt/dims/bin/dims_functions.sh:1064): parse_fqdn(): read -a fields
# +++(/opt/dims/bin/dims_functions.sh:1064): parse_fqdn():        echo --tags
# +++(/opt/dims/bin/dims_functions.sh:1064): parse_fqdn():        sed 's/\./ /g'
# ++(/opt/dims/bin/dims_functions.sh:1065): parse_fqdn(): '[' 1 -eq 1 ']'
# ++(/opt/dims/bin/dims_functions.sh:1066): parse_fqdn(): echo ''
# ++(/opt/dims/bin/dims_functions.sh:1067): parse_fqdn(): return 1
# +(/opt/dims/bin/dims_functions.sh:328): is_fqdn():      _tmp=
# +(/opt/dims/bin/dims_functions.sh:329): is_fqdn():      debug 'is_fqdn: _tmp='
# +(/opt/dims/bin/dims_functions.sh:216): debug():        [[ ! -z 0 ]]
# +(/opt/dims/bin/dims_functions.sh:216): debug():        [[ 0 -eq 0 ]]
# +(/opt/dims/bin/dims_functions.sh:217): debug():        echo '[+] DEBUG: is_fqdn: _tmp='
# [+] DEBUG: is_fqdn: _tmp=
# +(/opt/dims/bin/dims_functions.sh:218): debug():        return 0
# +(/opt/dims/bin/dims_functions.sh:330): is_fqdn():      [[ '' != '' ]]
# +(/opt/dims/bin/dims_functions.sh:333): is_fqdn():      return 1
# ++(/opt/dims/bin/dims.ansible-playbook:435): main():    compose_fqdn dimsdemo1 devops develop
# ++(/opt/dims/bin/dims_functions.sh:1126): compose_fqdn():       [[ 3 -ne 3 ]]
# ++(/opt/dims/bin/dims_functions.sh:1126): compose_fqdn():       [[ -z dimsdemo1 ]]
# ++(/opt/dims/bin/dims_functions.sh:1126): compose_fqdn():       [[ -z devops ]]
# ++(/opt/dims/bin/dims_functions.sh:1126): compose_fqdn():       [[ -z develop ]]
# ++(/opt/dims/bin/dims_functions.sh:1129): compose_fqdn():       echo dimsdemo1.devops.develop
# +(/opt/dims/bin/dims.ansible-playbook:435): main():     FQDN=dimsdemo1.devops.develop

# (This is a Bash internal variable)
export PS4='+(${BASH_SOURCE}:${LINENO}): ${FUNCNAME[0]:+${FUNCNAME[0]}():    }'

# Location of the error in the calling script.
function _error_location() {
    local _caller=$(caller 1)
    [[ ! -z "$_caller" ]] && echo "$_caller" | awk '{print "(" $3 ":" $1 ")";}'
}

function _caller_script_directory() {
    local _caller1=$(caller 1)
    local _c3=$(echo "$_caller1" | awk '{print $3;}')
    [[ -z "$c3" ]] && echo "?"
    [[ ! -z "$_caller1" ]] && echo $(dirname $_c3)
}

function error_exit() {
    local retval=$1 && shift
    if [[ $retval -eq 0 ]]; then
       echo "[!] !!! error_exit called with return code 0" >&2
       retval=42
    fi
    echo -n "[-] " >&2
    [[ $FLAGS_debug -eq ${FLAGS_TRUE} ]] && echo -n "$(_error_location) " >&2
    echo "$@" >&2
    exit $retval
}

# Code for the on_exit functionality derived from:
# http://www.linuxjournal.com/content/use-bash-trap-statement-cleanup-temporary-files
#
# WARNING!!! This functionality relies on use of a global array
# 'on_exit_items', which is set within the on_exit() function.
# That means that on_exit() CANNOT -- eith directly, or
# indirectly -- be called within a sub-shell. Doing so will
# only alter the array in the sub-shell, not the calling shell.
# This means inline command substitution with $(some_function) or
# `some_function` that in turn calls add_on_exit, will not result
# in the desired action being performed.

# (This is an internal variable)
declare -a on_exit_items

# NOTE: This function CANNOT be called within a subshell.
function on_exit()
{
    debug "Entering on_exit()"
    for i in "${on_exit_items[@]}"
    do
        debug "on_exit() performing: $i"
        eval $i
    done
    # Unset the trap, since it was just invoked
    cancel_on_exit
}

function cancel_on_exit() {
    trap - EXIT SIGHUP SIGINT SIGQUIT SIGTERM
}

# NOTE: This function CANNOT be called within a subshell.
function add_on_exit()
{
    local n=${#on_exit_items[*]}
    debug "Adding on_exit_item \"$*\""
    on_exit_items[$n]="$*"
    if [[ $n -eq 0 ]]; then
        debug "Setting trap on_exit()"
        trap on_exit EXIT SIGHUP SIGINT SIGQUIT SIGTERM
    fi
}

function clear_on_exit()
{
    on_exit_items=( )
}

function get_on_exit()
{
    local -a _array=( "${on_exit_items[@]}" )
    declare -p _array | sed -e 's/^declare -a _array=//'
}

#HELP get_true()
#HELP     Return the word "true" if $1 is 0, otherwise return "false".
#HELP     This converts Bash style return codes to a string.
get_true() {
    case $1 in
        0) echo 'true' ;;
        *) echo 'false' ;;
    esac
}

_log () {
    _BASH_SOURCE=`basename "${1}"` && shift
    _LINENO=${1} && shift
    echo "(${_BASH_SOURCE}:${_LINENO}) $@"
}

#HELP
#HELP plural_s()
#HELP    Provide a plural 's' inline (no newline) for proper grammarization
#HELP    usage: echo "I have 1 thing$(plural_s 1), I have 2 thing$(plural_s 2)."
#HELP           I have 1 thing, I have 2 things.
plural_s() {
    local n=$1
    if [[ -z "$n" ]]; then
        echo -n "" && return 1
    elif [[ $n -eq 1 ]]; then
        echo -n "" && return 0
    else
        echo -n "s" && return 0
    fi
}

#HELP
#HELP default_enable_verbose()
#HELP     This function allows the default for verbosity to be set on a
#HELP     per-program basis by checking to see if the calling program is
#HELP     listed in $HOME/.ELS_DEFAULT_VERBOSE with the value 1. If so,
#HELP     verbosity defaults to enabled (otherwise, disabled). The
#HELP     command line option --verbose can be used to set as desired
#HELP     at run time. Use with shflags as:
#HELP        DEFINE_boolean 'verbose' $(default_enable_verbose) 'be verbose' 'v'
default_enable_verbose() {
    if [[ ! -f $ELS_DEFAULT_VERBOSE ]]; then
        echo 'false'
        return 1
    fi
    local _default=$(cat ${ELS_DEFAULT_VERBOSE} | awk -F: "
BEGIN { e=0; }
/$BASE/ { print \$2; exit; }
END { print e; }
    ")
    [[ "$_default" == "1" ]] && echo 'true' || echo 'false'
    return 0
}

#HELP
#HELP default_enable_debug()
#HELP     This function allows the default for debugging to be set on a
#HELP     per-program basis by checking to see if the calling program is
#HELP     listed in $HOME/.ELS_DEFAULT_DEBUG with the value 1. If so,
#HELP     verbosity defaults to enabled (otherwise, disabled). The
#HELP     command line option --debug can be used to set as desired
#HELP     at run time. Use with shflags as:
#HELP        DEFINE_boolean 'debug' $(default_enable_debug) 'debug mode' 'v'
default_enable_debug() {
    if [[ ! -f $ELS_DEFAULT_DEBUG ]]; then
        echo 'false'
        return 1
    fi
    local _default=$(cat ${ELS_DEFAULT_DEBUG} | awk -F: "
BEGIN { e=0; }
/$BASE/ { print \$2; exit; }
END { print e; }
    ")
    [[ "$_default" == "1" ]] && echo 'true' || echo 'false'
    return 0
}

#HELP
#HELP els_main_init()
#HELP     Initialize Elsevier project scripts by handling common shflags setup
#HELP     operations related to --debug, --verbose, etc. Doing things in
#HELP     this function allows less DRY coupling of logic across many
#HELP     scripts.
els_main_init() {
    # Process flags that just return something and exit
    [[ ${FLAGS_help} -eq ${FLAGS_TRUE} ]] && exit 0
    [[ ${FLAGS_usage} -eq ${FLAGS_TRUE} ]] && usage && exit 0
    [[ ! -z ${FLAGS_version} && ${FLAGS_version} -eq ${FLAGS_TRUE} ]] && version && exit 0
    debug "$PROGRAM enabled DEBUG mode"
    # If both --debug and --verbose, set tracing
    [[ ${FLAGS_debug} -eq ${FLAGS_TRUE} && ${FLAGS_verbose} -eq ${FLAGS_TRUE} ]] && set -x
}

#HELP
#HELP verbose_enabled()
#HELP     Return Bash true (0) if verbose is enabled, otherwise
#HELP     false (1).
verbose_enabled() {
    [[ ! -z ${FLAGS_verbose} && ${FLAGS_verbose} -eq ${FLAGS_TRUE} || $ELS_VERBOSE -eq 1 ]]
}

# This function expects use of shFlags.
#HELP
#HELP verbose()
#HELP     Output the command line arguments as a string if verbose is
#HELP     enabled to stdout.  Output looks like:
#HELP       [+] The arguments of the call
verbose() {
    verbose_enabled && echo "[+] $(echo $@ | sed 's/[     ]\+/ /g')"
    return 0
}

#HELP
#HELP debug_enabled() {
#HELP     Return Bash true (0) if verbose is enabled, otherwise
#HELP     false (1).
debug_enabled() {
    [[ ! -z ${FLAGS_debug} && ${FLAGS_debug} -eq ${FLAGS_TRUE} || $ELS_DEBUG -eq 1 ]]
}

#HELP
#HELP debug()
#HELP     Produce debugging output on stderr from $@ if debugging is enabled.
#HELP     Output on stderr looks like:
#HELP       [+] DEBUG: The arguments of the call
debug() {
    debug_enabled && echo "[+] DEBUG: $@" >&2
    return 0
}

#HELP
#HELP warn()
#HELP     Produce a string that looks the same as the error_exit() output on
#HELP     stderr and return (rather than exit).
#HELP     Output on stderr looks like:
#HELP       [-] The arguments of the call
warn() {
    echo "[-] $(echo $@ | sed -e 's/[[:blank:]]\+/ /g' -e 's/[[:blank:]][[:blank:]]*$//')" >&2
    return 0
}

#HELP
#HELP say()
#HELP     Output all args passed to function, eliminating any repeated whitespace,
#HELP     to stdout. This allows multi-line output with lots of whitespace to be
#HELP     cleaner. (See also: say_raw()) Output on stdout looks like:
#HELP       [+] The arguments of the call
say() {
    #echo "[+] $(echo $@ | sed -e 's/[     ]\+/ /g' -e 's/  *$//')"
    echo "[+] $(echo $@ | sed -e 's/[[:blank:]]\+/ /g' -e 's/[[:blank:]][[:blank:]]*$//')"
    return 0
}

#HELP
#HELP say_raw()
#HELP     Output the string passed to function as $1, without any processing, with
#HELP     formatting like verbose() on stdout.
#HELP     (See also: say()) Output on stdout looks like:
#HELP       [+] The   contents   of   first    arg    with   all   these   spaces
say_raw() {
    printf "[+] %s" "$1"
    return 0
}

#HELP
#HELP usage()
#HELP    Placeholder function that simple returns a message that
#HELP    usage() is not defined. (Override this function in your own
#HELP    script after sourcing this file.)
function usage() {
    say "Function usage() is not defined"
}

#HELP
#HELP get_help_text()
#HELP     Extract help text from a file, where "help text" is identified by lines
#HELP     that begin with "#HELP ". Identify those lines, and strip that line
#HELP     identifier from them, to produce self-documenting help text. This is used
#HELP     by both Makefile and Bash scripts.

function get_help_text() {
    local fname=$1
    [[ -f $fname ]] || error_exit 1 "get_help_text(): file does not exist: $fname"
    say "Help text for $fname"
    say ""
    say "Global variables (local or exported)"
    say ""
    egrep "^#HELP_Global" $fname |
        sed -e 's/#HELP_//' |
        sort
    say ""
    say "Functions and usage"
    say ""
    egrep "^#HELP$|#HELP " $fname |
        sed -e 's/#HELP //' -e 's/#HELP//'
}

function get_num_pages_of_item()
{
        local __git_user_option=$1
        local __link=$2
        num_pages=0

        echo $(curl -s -I ${__git_user_option} ${__link} | grep Link: | awk '{print $4}' | awk -F= '{print $2}' | sed 's/>;$//')
}
