#!/bin/bash

# Source helper libraries
. $ELS/lib/shflags/src/shflags
. $ELS/bin/elsevier_functions.sh

# Define command line options
DEFINE_boolean 'debug' false 'enable debug mode' 'd'
DEFINE_boolean 'usage' false 'print usage information' 'u'
DEFINE_boolean 'verbose' false 'be verbose' 'v'
# Define further command line options here
DEFINE_string 'repo' '' 'repo' 'r'
DEFINE_string 'branch' '' 'branch' 'b'
DEFINE_string 'git-user-option' "${GIT_USER_API}" 'git user option to pass to curl' 'g'
DEFINE_boolean 'pages' false 'determine pages of info' 'p'

FLAGS_HELP="usage: $BASE [options] args"

# Define functions

usage() {
    flags_help
    cat << EOD

This script is intended to quickly test the functionality of both shflags
and the Github API commands.

Running this script with no arguments results in a message indicating which
flags are required to run the script.

To test retrieving information about a repo using the Github API, use the
--repo option like this:

  $ test_git_api.sh --repo clot-catalog-api

To test retrieving information about a specific branch of a given repo,
use the --repo and --branch option like this:

  $ test_git_api.sh --repo clot-catalog-api --branch develop 

Using --verbose enables verbose output in this script and [ ].
Using --debug enables debugging output in this script and [ ].
Using both --verbose and --debug gives max output and [ ].

EOD

    exit 0
}

# Locally defined functions here




# main

main()
{
    els_main_init

    # Do what is needed with other flags here (i.e., run script)
    [[ ! -z "${FLAGS_branch}" && -z "${FLAGS_repo}" ]] &&
        error_exit 1 "--repo not specified: must accompany --branch"
    if [[ -z "${FLAGS_repo}" && -z "${FLAGS_branch}" ]]; then
        if [[ ${FLAGS_pages} -eq ${FLAGS_TRUE} ]]; then
            get_num_pages_of_item ${ELSREPOURL}
            echo "[+] Number of pages of repos for Github project elsevierPTG is $num_pages"
        else
            error_exit 1 "must supply --repo and/or --branch or ask for --pages of repos of elsevierPTG project"
        fi
    fi

    if [[ ! -z "${FLAGS_repo}" && -z "${FLAGS_branch}" && ${FLAGS_pages} -eq ${FLAGS_FALSE} ]]; then
        verbose "Printing first page of information about repo ${FLAGS_repo}"
        curl -s ${FLAGS_git_user_option} https://api.github.com/repos/elsevierPTG/${FLAGS_repo}
    elif [[ ! -z "${FLAGS_repo}" && ! -z "${FLAGS_branch}" && ${FLAGS_pages} -eq ${FLAGS_FALSE} ]]; then
        verbose "Printing first page of information about branch ${FLAGS_branch} on repo ${FLAGS_repo}"
        curl -s ${FLAGS_git_user_option} https://api.github.com/repos/elsevierPTG/${FLAGS_repo}/branches/${FLAGS_branch}
    fi

    if [[ ${FLAGS_pages} -eq ${FLAGS_TRUE} && ! -z ${FLAGS_repo} ]]; then
        get_num_pages_of_item ${INDREPOURL}/${FLAGS_repo}/branches
        echo "[+] Number of pages of branches on repo ${FLAGS_repo} is $num_pages"
    fi

   
    debug "Returning from main()"
    on_exit
    return $?
}


# parse the command line
FLAGS "$@" || exit $?
eval set -- "${FLAGS_ARGV}"
main "$@"
exit $?    
