import pandas as pd
from ChromaTone.markov.markov_chain import SecondOrderMarkovModel

if __name__ == "__main__":
    scales = ["maj", "min"]
    trends = [0,1,2,3]
    combinations = [(scale, trend) for scale in scales for trend in trends]

    df = pd.read_csv("motifs_df/midi_motives.csv")

    # Iterate through each combination
    for scale, trend in combinations:
            
        # Filter the DataFrame for the current combination
        df_filtered = df[(df["direction"] == trend) & (df["scale"] == scale)]

        model = SecondOrderMarkovModel()
        model.train(df_filtered["midi_notes"])
        model.save_model(f"models/markov-{scale}-{trend}.pkl")
