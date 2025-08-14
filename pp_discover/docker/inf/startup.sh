#!/bin/bash

# Exit on error and treat unset variables as errors
set -e
set -u

# Start the SSH service
sudo service ssh start

# Activate the Conda environment
source /home/user/miniconda3/bin/activate pp_api_env

# Capture CMD arguments
CMD_ARGS="$@"

# Log the received arguments for debugging
echo "Received arguments: $CMD_ARGS"

# Run worker script with CMD arguments
python pp_api.py $CMD_ARGS
