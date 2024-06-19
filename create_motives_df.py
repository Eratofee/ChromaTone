from pathlib import Path
import pandas as pd

def create_motives_df(midi_path):
    df = pd.DataFrame(columns=["file_path", "direction", "scale"])

    # Iterate through the files in the directory
    for file in midi_path.iterdir():
        if file.is_file():
            # Split the file name to extract the scale and direction
            file_info = file.stem.split(" ")
            scale = file_info[0]
            direction = file_info[1]
            
            # Append the extracted information to the DataFrame
            df.loc[len(df)] = [file, direction, scale]

    # Display the DataFrame
    df.to_csv("midi_motives.csv", index=False)

if __name__ == "__main__":

    midi_path = Path("chromaTone_midi_files")
    create_motives_df(midi_path)