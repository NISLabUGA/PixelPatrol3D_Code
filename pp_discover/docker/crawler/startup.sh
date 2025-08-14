#!/bin/bash

# Exit on error and treat unset variables as errors
set -e
set -u

# # Add Miniconda to PATH
# export PATH="/home/user/miniconda3/bin:$PATH"

# Start the SSH service
sudo service ssh start

# Remove existing X11-related files
rm -f /tmp/.X11-unix/X1
rm -f /tmp/.X1-lock

# Password: vncuser
# Start the VNC server
vncserver -geometry 1920x1080 -depth 16 :1

# No longer need it. Added it to V2
# pip install pandas

# Capture CMD arguments
CMD_ARGS="$@"

# Log the received arguments for debugging
echo "Received arguments: $CMD_ARGS"

# Run worker script with CMD arguments
python crawl_url.py $CMD_ARGS
