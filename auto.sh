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
    arg1=$(echo $line | cut -d'|' -f1 | xargs) # xargs trims leading/trailing spaces
    arg2=$(echo $line | cut -d'|' -f2 | xargs)
    arg3=$(echo $line | cut -d'|' -f3 | xargs)

    # Run the command with the arguments
    make video ARGS="--prompt \"$arg1\" --director mvp_director --output \"$arg2\" --actors \"$arg3\""
    
done < "$input_file"

