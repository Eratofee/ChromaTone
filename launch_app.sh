#!/bin/bash

# Function to handle Ctrl+C and kill background processes
cleanup() {
    echo "Terminating scripts..."
    kill $pid1 $pid2
}

# Trap SIGINT (Ctrl+C)
trap cleanup SIGINT

# Start the first script in the background
python connect_async.py &
pid1=$!

# Start the second script in the background
python drawing.py &
pid2=$!

# Wait for both scripts to finish
wait $pid1
wait $pid2
