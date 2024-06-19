import socket
import time
import errno
import json
import random
import numpy as np

# PD Socket
UDP_IP = 'localhost'
UDP_PORT = 9082
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Probabilities Socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('localhost', 12345))
s.listen()
s.setblocking(False)

pause = 0.5


PITCH_CLASSES = ["c", "d_b", "d", "e_b", "e", "f", "g_b","g", "a_b", "a", "b_b", "b"]
oktave = 5
MIDI_MULTIPLIER = oktave*15

midis = [i for i in range(MIDI_MULTIPLIER, MIDI_MULTIPLIER+len(PITCH_CLASSES))]
translation_pit_2_midi = dict(zip(PITCH_CLASSES, midis))

# Example note range
note_range = list(range(60, 72))  # C4 to B4

probabilities = None

def check_for_incoming_data():
    print("Checking for incoming data")
    global probabilities
    try:
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            data = conn.recv(1024)
            if data:
                probabilities = json.loads(data.decode('utf-8'))
                print("Received probabilities:", probabilities)
    except socket.error as e:
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('Socket error:', e)

def generate_note():
    print("Generating note")
    if probabilities:
        print("Generating note with probabilities")
        return translation_pit_2_midi[np.random.choice(a = PITCH_CLASSES, p = probabilities, size = 1)[0]]
    else:
        print("Failed to generate note")
        return None  # Default to random note if no probabilities

while True:
    check_for_incoming_data()
    
    note = generate_note()
    
    if note:
        # Convert the note to bytes
        print(note)
        note_bytes = note.to_bytes(1, 'big') 
        
        # Send the bytes over UDP
        sock.sendto(note_bytes, (UDP_IP, UDP_PORT))
        
    # Pause
    time.sleep(pause)