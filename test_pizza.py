import time
import mido
from mido import Message, MidiFile, MidiTrack

# Set up the output port
output_port_name = 'IAC pizza'
outport = mido.open_output(output_port_name)

# Function to send a MIDI note
def send_midi_note(note, velocity, duration):
    # Send a note on message
    msg = Message('note_on', note=note, velocity=velocity)
    outport.send(msg)
    time.sleep(duration)
    # Send a note off message
    msg = Message('note_off', note=note, velocity=velocity)
    outport.send(msg)

# Example usage: send a middle C note (note number 60) with velocity 64 for 1 second
send_midi_note(note=60, velocity=64, duration=1)

# Close the port
outport.close()