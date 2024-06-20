import random
import numpy as np
import ast
import pickle
from collections import defaultdict, Counter

class SecondOrderMarkovModel:
    def __init__(self, notes=None):
        self.transition_counts = defaultdict(Counter)
        self.transition_probabilities = defaultdict(dict)
        if notes is not None:
            self.train(notes)
    
    def train(self, sequences_notes):
        # Populate the transition counts
        for note_seq in sequences_notes:
            note_seq = np.array(ast.literal_eval(note_seq))
            note_seq = np.append(-1, note_seq)
            for i in range(len(note_seq) - 2):
                state = (note_seq[i], note_seq[i+1])
                next_note = note_seq[i+2]
                self.transition_counts[state][next_note] += 1
        
        # Convert counts to probabilities
        self._calculate_probabilities()
    
    def _calculate_probabilities(self):
        for state, next_notes in self.transition_counts.items():
            total = sum(next_notes.values())
            for next_note, count in next_notes.items():
                self.transition_probabilities[state][next_note] = count / total
    
    def generate_sequence(self, start_notes, length):
        if len(start_notes) != 2:
            raise ValueError("start_notes must contain exactly two notes")
        
        sequence = list(start_notes)
        
        for _ in range(length - 2):
            state = (sequence[-2], sequence[-1])
            if state in self.transition_probabilities:
                next_notes = list(self.transition_probabilities[state].keys())
                probabilities = list(self.transition_probabilities[state].values())
                next_note = random.choices(next_notes, probabilities)[0]
                sequence.append(next_note)
            else:
                print("Warning, no transition avaliuable")
                break  # No transition available, stop the sequence
        
        return sequence
    
    def save_model(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump({
                'transition_counts': self.transition_counts,
                'transition_probabilities': self.transition_probabilities
            }, f)
    
    def load_model(self, filename):
        with open(filename, 'rb') as f:
            model_data = pickle.load(f)
            self.transition_counts = model_data['transition_counts']
            self.transition_probabilities = model_data['transition_probabilities']


