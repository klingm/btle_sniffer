#!/bin/sh

script_path=$(dirname `which $0`)

py3=`which python3`
if [ $? -ne 0 ]; then
    # If it's not in the PATH, assume it's in /usr/local/bin
    py3="/usr/local/bin/python3"
fi

# default to a single iteration
iterations=1

# get arg for number of iterations
while getopts "i:" opt; do
    case "$opt" in
    i)  iterations=$OPTARG
        ;;
    esac
done

echo Running $iterations times

i=0
while [ $i -lt $iterations ]
do
    echo $i/$iterations
    $py3 $script_path/btle_sniffer.py "$@"
    sleep 1
    i=`expr $i + 1`
done