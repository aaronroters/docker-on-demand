#!/bin/bash

# Define the variable value
port=8080

# Define the source and destination file paths
source_file="boilerplate.config"
destination_file="new.config"

# Read the contents of the source file
contents=$(<"$source_file")

# Replace the variable placeholder with the actual value
updated_contents="${contents/\${port}/$port}"

# Write the updated contents to the destination file
echo "$updated_contents" > "$destination_file"