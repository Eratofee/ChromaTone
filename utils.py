import pandas as pd
import json
import random

UP = 0
DOWN = 1
VARYING = 2
CONSTANT = 3
OFF = 4

color_ranges = {
    'red': [(0, 10), (166, 180)], 
    'orange': (11, 23),
    'yellow': (24, 37),
    'spring_green': (38, 55),
    'green': (56, 68),
    'turquoise': (69, 82),
    'cyan': (83, 99),
    'ocean': (100, 113),
    'blue': (114, 127),
    'violet': (128, 145),
    'magenta': (146, 165)
}

color_notes = {
    "c": "white",
    "d_b": "ocean",
    "d": "turquoise",
    "e_b": "orange",
    "e": "yellow",
    "f": "green",
    "g_b": "spring_green",
    "g": "blue",
    "a_b": "cyan",
    "a": "red",
    "b_b": "magenta",
    "b": "violet"
}

notes_colors = {
    "white": "c",
    "ocean": "d_b",
    "turquoise": "d",
    "orange": "e_b",
    "yellow": "e",
    "green": "f",
    "spring_green": "g_b",
    "blue": "g",
    "cyan": "a_b",
    "red": "a",
    "magenta": "b_b",
    "violet": "b"
}

PITCH_CLASSES = ["c", "d_b", "d", "e_b", "e", "f", "g_b","g", "a_b", "a", "b_b", "b"]

def print_trend(trend):
    if trend == UP:
        print("Trend: Up")
    elif trend == DOWN:
        print("Trend: Down")
    elif trend == CONSTANT:
        print("Trend: Constant")
    elif trend == VARYING:
        print("Trend: Varying")
    else:
        print("Trend: Off")
        
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