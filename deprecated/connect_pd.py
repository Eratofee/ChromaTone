import socket
import time
import errno
import json
from drawing import print_trend
import random
import pandas as pd
import numpy as np
import ast  # Import ast module to parse strings into lists/arrays

UP = 0
DOWN = 1
VARYING = 2
CONSTANT = 3
OFF = 4

# PD Socket
UDP_IP = 'localhost'
UDP_PORT = 8000
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Probabilities Socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('localhost', 12346))
s.listen()
s.setblocking(False)

pause = .4

PITCH_CLASSES = ["c", "d_b", "d", "e_b", "e", "f", "g_b","g", "a_b", "a", "b_b", "b"]
oktave = 5
MIDI_MULTIPLIER = oktave*15

midis = [i for i in range(MIDI_MULTIPLIER, MIDI_MULTIPLIER+len(PITCH_CLASSES))]
translation_pit_2_midi = dict(zip(PITCH_CLASSES, midis))

# Example note range
note_range = list(range(60, 72))  # C4 to B4

probabilities = None
trend = None
scale = 'Min'

def check_for_incoming_data():
    print("Checking for incoming data")
    global probabilities
    global trend
    global scale
    try:
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            data_buffer = b""
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                data_buffer += data
            if data_buffer:
                received_data = json.loads(data_buffer.decode('utf-8'))
                probabilities = received_data.get("pitch_probabilities")
                trend = received_data.get("trend")
                scale = received_data.get("scale")
                print("Received probabilities:", probabilities)
                print("Received:")
                print_trend(trend=trend)
                print("Received scale:", scale)
    except socket.error as e:
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('Socket error:', e)

midi_motives = pd.read_csv("midi_motives.csv")

def choose_motif():
    if probabilities:
        print("Generating note")
        key_ind = np.argmax(probabilities)
        key = PITCH_CLASSES[key_ind]
        print("Key is", key)
        # print("Trend is", trend)
        print_trend(trend=trend)
        if trend == 4:
            return None
        df_filtered = midi_motives[(midi_motives["direction"] == trend) & (midi_motives["scale"] == scale)]
        random_row = df_filtered.sample()
        midi_notes = random_row["midi_notes"].iloc[0]
        return np.array(ast.literal_eval(midi_notes)) + key_ind
    else:
        print("Failed to generate note")
        return None  # Default to random note if no probabilities

while True:
    check_for_incoming_data()
    
    notes = choose_motif()
    print("received sequence")
    if notes is not None:
    # if notes is not None:
        for note in notes:
        # Convert the note to bytes
            # note += 12
            print(note)

            note_bytes = note.tobytes() 
            
            # Send the bytes over UDP
            sock.sendto(note_bytes, (UDP_IP, UDP_PORT))

            # Pause
            time.sleep(pause)

    check_for_incoming_data()
    