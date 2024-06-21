import numpy as np
import pandas as pd
import ast
from markov.markov_chain import MarkovManager
from utils import sample_initial_note

PITCH_CLASSES = ["c", "d_b", "d", "e_b", "e", "f", "g_b", "g", "a_b", "a", "b_b", "b"]
oktave = 5
MIDI_MULTIPLIER = oktave * 15

midis = [i for i in range(MIDI_MULTIPLIER, MIDI_MULTIPLIER + len(PITCH_CLASSES))]
translation_pit_2_midi = dict(zip(PITCH_CLASSES, midis))
midi_motives = pd.read_csv("motifs_df/midi_motives.csv")

CONSTANT = 3
OFF = 4

class MotifGen:
    def __init__(self, with_markov=False):
        self.markov_manager = MarkovManager()
        self.probabilities = None
        self.with_markov: bool = with_markov
        self.scale = None
        self.trend = CONSTANT
        self.duration = 0.35
        self.active_color_flag = False
        self.key = None

    def set_active_color_flag(self, active_color_flag):
        self.active_color_flag = active_color_flag

    def set_key(self, key):
        self.key = key

    def set_probabilities(self, probabilities):
        self.probabilities = probabilities

    def set_trend(self, trend):
        self.trend = trend

    def set_scale(self, scale):
        self.scale = scale

    def set_duration(self, duration):
        self.duration = duration

    def get_trend(self):
        return self.trend
    
    def get_duration(self):
        return self.duration

    def choose_motif(self):
        # Check if probabilities have been set
        if self.probabilities:
            # Determine the key index based on active color flag
            if self.active_color_flag:
                # Use the provided key
                key = self.key
                key_ind = PITCH_CLASSES.index(key)
                key_ind = np.array([key_ind])
            else:
                # Find the key index with the highest probability
                key_ind = np.argmax(self.probabilities)
                key = PITCH_CLASSES[key_ind]
            
            print("Key is", key)
            
            # If trend is OFF, return None to indicate no motif should be generated
            if self.trend == OFF:
                return None
            if self.with_markov:
                # markov implementation --> Work in progress
                initial_note = sample_initial_note(direction=int(self.trend), scale=str(self.scale))
                markov_model = self.markov_manager.get_model(trend=self.trend, scale=self.scale)
                markov_seq = markov_model.generate_sequence([-1, initial_note], 9)
                return markov_seq + key_ind, self.duration, self.trend, translation_pit_2_midi[key] - 24

            # Filter the midi_motives DataFrame based on the trend and scale
            df_filtered = midi_motives[(midi_motives["direction"] == self.trend) & (midi_motives["scale"] == self.scale)]
            
            # If no matching rows are found, return None
            if df_filtered.empty:
                return None
            
            # Randomly select one row from the filtered DataFrame
            random_row = df_filtered.sample()
            # Extract the MIDI notes from the selected row
            midi_notes = random_row["midi_notes"].iloc[0]
            
            # Return the transposed MIDI notes, duration, trend, and transposed key index
            return np.array(ast.literal_eval(midi_notes)) + key_ind, self.duration, self.trend, translation_pit_2_midi[key] - 24
        else:
            # If probabilities are not set, print an error message and return None
            print("Failed to generate note")
            return None, None, None, None

