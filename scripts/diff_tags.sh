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
DEFINE_string 'tagA' '' 'name of initial tag to diff' 'A'
DEFINE_string 'tagB' '' 'name of final tag to dif' 'B'

FLAGS_HELP="usage: $BASE [options] args"

# Define functions

usage() {
    flags_help
    cat << EOD

This script is intended to return a list of commits from a given repo between two
tags in a file called \$repo-\$tagA..\$tagB-diff located in $ELS/commits.

You must give a repo name and two tags to diff.

  $ diff_tags.sh --repo eols-automation --tagA v1.0 --tagB v2.0

Using --verbose enables verbose output in this script.
Using --debug enables debugging output in this script.
Using both --verbose and --debug gives max output.

EOD

    exit 0
}

# Locally defined functions here
function print_page()
{
    local __git_user_option=$1
    local __link=$2
    local __output_file=$3

    #curl -s ${__git_user_option} ${__link} | jq '.[] | .sha, .commit.message' >> ${__output_file}
    curl -s ${__git_user_option} ${__link}  | jq '. | .commits' | jq '.[] | .sha, .commit.message' >> ${__output_file}
    return $?
}


# main

main()
{
    els_main_init

    # Variables
    OUTPUTPATH="$ELS/commits"

    if [[ ! -d "$OUTPUTPATH" ]]; then
        mkdir -p "$OUTPUTPATH"

        if [[ $? -ne 0 ]]; then
            error_exit 1 "failed to create directory $OUTPUTPATH"
        fi
    fi

    # Do what is needed with other flags here (i.e., run script)
    [[ -z "${FLAGS_repo}" && -z "${FLAGS_tagA}" && -z "${FLAGS_tagB}" ]] &&
        error_exit 1 "--repo, --tagA, and --tagB must be specified"

    [[ ! -z "${FLAGS_repo}" && -z "${FLAGS_tagA}" && -z "${FLAGS_tagB}" ]] &&
        error_exit 1 "--tagA and --tagB must be specified"

    [[ ! -z "${FLAGS_repo}" && -z "${FLAGS_tagA}" && ! -z "${FLAGS_tagB}" ]] &&
        error_exit 1 "--tagA must be specified"

    [[ ! -z "${FLAGS_repo}" && ! -z "${FLAGS_tagA}" && -z "${FLAGS_tagB}" ]] &&
        error_exit 1 "--tagB must be specified"

    # Determine number of pages of commits in diff
    pages_of_commits=$(get_num_pages_of_item "${FLAGS_git_user_option}" "$INDREPOURL/${FLAGS_repo}/compare/${FLAGS_tagA}...${FLAGS_tagB}")
    if [[ -z "$pages_of_commits" ]]; then
        pages_of_commits=1
    fi

    # Send each page of commit info to OUTPUTFILE
    DATE=$(date +%s)
    OUTPUTFILE="$OUTPUTPATH/${FLAGS_repo}-${FLAGS_tagA}..${FLAGS_tagB}-diff-$DATE"
    OUTPUTTMP="$OUTPUTPATH/tmp"

    for page in $(seq 1 $pages_of_commits);
    do
        #print_page "${FLAGS_git_user_option}" "$INDREPOURL/${FLAGS_repo}/commits?sha=${FLAGS_branch}&page=$page" "$OUTPUTFILE"
        print_page "${FLAGS_git_user_option}" "$INDREPOURL/${FLAGS_repo}/compare/${FLAGS_tagA}...${FLAGS_tagB}?page=$page" "$OUTPUTFILE"
    done

    # Clean up
    # Put hashes and messages on same lines
    sed -i "" "N;s/\n/ /" $OUTPUTFILE

    # Remove extraneous quotes
    sed -i "" "s/\"//g" $OUTPUTFILE

    # Shorten commit hashes
    awk '{ $1 = substr($1, 1, 7) } 1' $OUTPUTFILE > $OUTPUTPATH/tmp && mv $OUTPUTTMP $OUTPUTFILE

    debug "Returning from main()"
    on_exit
    return $?
}


# parse the command line
FLAGS "$@" || exit $?
eval set -- "${FLAGS_ARGV}"
main "$@"
exit $?    
