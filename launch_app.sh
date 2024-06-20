#!/bin/bash

# Execute the first Python script
python connect_pd_async.py

# Check if the first script executed successfully
if [ $? -eq 0 ]; then
    # Execute the second Python script if the first one succeeded
    python drawing.py
else
    # Print an error message if the first script failed
    echo "connect_pd_async.py failed to execute."
    exit 1
fi
