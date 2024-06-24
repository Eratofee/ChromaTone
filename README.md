# ChromaTone
## Overview

Chromatone is an application that allows users to create melodies based on their digital drawings. By utilizing the Markov Chain algorithm, the app translates visual information from the canvas into musical notes, generating unique melodies for each drawing. 

## Components
- **Digital Canvas**: A user-friendly interface to create drawings.
    
- **Melody Generation**: Converts visual elements of the drawing into musical notes in real-time using Markov Chains.

## Installation

### Prerequisites
- Python 3.12 or higher
- pip (Python package installer)

### Install requirements
Run the following command to install the necessary Python packages:
```bash
pip install -r requirements.txt
```

### Train Models
- Original Motifs: Located in ./chromaTone_midi_files, these are the base melodies for training.
- Pre-processed Data: The ./motifs_df directory contains both the preprocessing code and the processed motifs data. This data is crucial for training the Markov models.
- Markov Chain Implementation: The implementation of the second-order Markov chain used in this project can be found in the ./markov directory.


### Setup Virtual Midi Ports
To send MIDI signals from ChromaTone, you must set up two virtual MIDI ports:
1. System-Specific Setup: The process for setting up virtual MIDI ports varies by operating system. Please consult your system's documentation for guidance.
2. Configuration: After setup, adjust the names of the two MIDI ports in the connect_async file's main function to match your system.


### Run app

1. DAW Setup: Open your preferred Digital Audio Workstation (DAW), set up two tracks with virtual instruments, and configure them to receive input from the virtual MIDI ports.
2. Launch ChromaTone: To start the application, execute:
```bash
./run_app.sh
```

## Usage
Once ChromaTone is running:
1. Create a Drawing: Use the digital canvas to draw. Your drawing will serve as the basis for the melody generation.
2. Generate Melody: ChromaTone will analyze your drawing and create a melody in real-time based on it.
3. Enjoy Your Music: The generated melody will play through your DAW. Experiment with different drawings to explore various musical outcomes.

## Troubleshooting
If you encounter issues:

- Verify Python and pip are correctly installed and updated.
- Ensure the virtual MIDI ports are correctly set up and named.
- Check that the DAW is correctly configured to receive MIDI signals from ChromaTone.
- For further assistance, please contact us directly.

## Contributing
Contributions to ChromaTone are welcome! Whether it's feature suggestions, bug reports, or code contributions, please feel free to reach out.
