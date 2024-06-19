from pathlib import Path
import pandas as pd
import mido
import numpy as np


direction_mapping = {"Asc" : 0, "Des" : 1, "Hor" : 3, "Osc" : 2}

def create_motives_df(midi_path):
    df = pd.DataFrame(columns=["file_path", "direction", "scale", "midi_notes"])

    # Iterate through the files in the directory
    for file in midi_path.iterdir():
        if file.is_file():
            # Split the file name to extract the scale and direction
            file_info = file.stem.split(" ")
            scale = file_info[0].lower()
            direction = file_info[1]
            encoded_direction = direction_mapping.get(direction)

            # Load MIDI file
            midi_file = mido.MidiFile(file)

            # Extract note numbers
            midi_notes = []
            for track in midi_file.tracks:
                for msg in track:
                    if msg.type == 'note_on':
                        midi_notes.append(msg.note)
            
            # Append the extracted information to the DataFrame
            df.loc[len(df)] = [file, encoded_direction, scale, midi_notes]

    # Display the DataFrame
    df.to_csv("midi_motives.csv", index=False)

if __name__ == "__main__":

    midi_path = Path("chromaTone_midi_files")
    create_motives_df(midi_path)