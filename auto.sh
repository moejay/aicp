#!/bin/bash

# Check if the filename is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: ./script.sh <input_file>"
    exit 1
fi

# File name
input_file=$1

# Check if the file exists
if [ ! -f "$input_file" ]; then
    echo "Error: File $input_file not found."
    exit 1
fi

# Read file line by line
while IFS= read -r line; do
    # Parse the arguments
    prompt=$(echo $line | cut -d'|' -f1 | xargs) # xargs trims leading/trailing spaces
    program=$(echo $line | cut -d'|' -f2 | xargs)
    director=$(echo $line | cut -d'|' -f3 | xargs)
    production=$(echo $line | cut -d'|' -f4 | xargs)
    output=$(echo $line | cut -d'|' -f5 | xargs)
    actors=$(echo $line | cut -d'|' -f6 | xargs)
	# actors are comma separated, let's convert them to "--actors actor1 --actors actor2 ..."
	actors=$(echo $actors | sed 's/,/ --actors /g')

    # Run the command with the arguments
    ARGS="--prompt \"$prompt\" --program \"$program\" --production-config $production --director $director --output \"$output\" --actors \"$actors\""
    
	echo "Running: with: $ARGS"
	make video ARGS="$ARGS"
    
done < "$input_file"

