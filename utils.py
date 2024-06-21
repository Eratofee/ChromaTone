import pandas as pd
import json
import random

def load_data(filepath):
    """Load the JSON data from a file."""
    with open(filepath, 'r') as file:
        data = json.load(file)
    return data

def get_initial_notes(data, direction, scale):
    """Get initial notes for given direction and scale from the data."""
    for entry in data:
        if entry['direction'] == direction and entry['scale'] == scale:
            return entry['initial_note']
    return None

def sample_initial_note(direction, scale):
    """Load data, find initial notes for given direction and scale, and randomly sample one note."""
    data = load_data('initial_notes.json')
    initial_notes = get_initial_notes(data, direction, scale)

    if initial_notes:
        sampled_note = random.choice(initial_notes)
        print(f"Randomly sampled note: {sampled_note}")
        return int(sampled_note)
    else:
        print(f"No initial notes found for direction {direction} and scale {scale}")
        return None