#!/bin/bash

. $ELS/lib/shflags/src/shflags
. $ELS/bin/elsevier_functions.sh

# Define command line options
DEFINE_boolean 'debug' false 'enable debug mode' 'd'
DEFINE_boolean 'usage' false 'print usage information' 'u'
DEFINE_boolean 'verbose' false 'be verbose' 'v'
# Define further command line options here

FLAGS_HELP="usage: $BASE [options] args"

# Define functions

usage() {
    flags_help
    cat << EOD

This script is intended to [ ]. Develop further information here.

Running this script with no arguments results in [ ].

To do something specific, run the script like this [ ].

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
    # if --verbose or --debug used alone, go with -vv, but if both used, crank up to -vvvv
    # if [[ $FLAGS_debug -eq ${FLAGS_TRUE} && $FLAGS_verbose -eq ${FLAGS_TRUE} ]]; then
    #    do something
    # elif [[ $FLAGS_debug -eq ${FLAGS_TRUE} || $FLAGS_verbose -eq ${FLAGS_TRUE} ]]; then
    #    do something a bit less
    # fi

    # Do what is needed with other flags here (i.e., run script)

    debug "Returning from main()"
    on_exit
    return $?
}


# parse the command line
FLAGS "$@" || exit $?
eval set -- "${FLAGS_ARGV}"
main "$@"
exit $?    
