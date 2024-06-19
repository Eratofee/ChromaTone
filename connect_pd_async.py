import socket
import time
import errno
import json
from drawing import print_trend
import random
import pandas as pd
import numpy as np
import ast
import asyncio

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
scale = 'min'

midi_motives = pd.read_csv("midi_motives.csv")

class UDPComm:
    def __init__(self, ip, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)
        self.ip = ip
        self.port = port

    async def send_note(self, note_bytes):
        loop = asyncio.get_running_loop()
        await loop.sock_sendto(self.sock, note_bytes, (self.ip, self.port))

class TCPComm:
    def __init__(self, ip, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((ip, port))
        self.sock.listen()
        self.sock.setblocking(False)
        self.probabilities = None
        self.trend = None
        self.scale = 'min'

    async def check_for_incoming_data(self):
        print("Listening for incoming data")
        while True:
            try:
                print("Inside Try block")
                conn, addr = self.sock.accept()
                with conn:
                    data_buffer = b""
                    while True:
                        print("Inside while with conn")
                        data = conn.recv(1024)
                        if not data:
                            break
                        data_buffer += data
                    if data_buffer:
                        received_data = json.loads(data_buffer.decode('utf-8'))
                        self.probabilities = received_data.get("pitch_probabilities")
                        self.trend = received_data.get("trend")
                        self.scale = received_data.get("scale")
                        print("Received data")
            except socket.error as e:
                if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                    print('Socket error:', e)
            await asyncio.sleep(1)

    def choose_motif(self):
        if self.probabilities:
            print("Generating note")
            key_ind = np.argmax(self.probabilities)
            key = PITCH_CLASSES[key_ind]
            print("Key is", key)
            # print("Trend is", trend)
            print_trend(trend=self.trend)
            if trend == 4:
                return None
            df_filtered = midi_motives[(midi_motives["direction"] == self.trend) & (midi_motives["scale"] == self.scale)]
            random_row = df_filtered.sample()
            midi_notes = random_row["midi_notes"].iloc[0]
            return np.array(ast.literal_eval(midi_notes)) + key_ind
        else:
            print("Failed to generate note")
            return None  # Default to random note if no probabilities

async def send_notes(udp_comm, tcp_comm):
    while True:
        notes = tcp_comm.choose_motif()
        if notes is not None:
            for note in notes:
                print(note)
                note += 12
                note_int = int(note)  # Convert to Python int
                note_bytes = note_int.to_bytes(2, byteorder='big')
                
                # Use the send_note method of the UDPComm instance
                await udp_comm.send_note(note_bytes)  # Removed loop
                
                # Pause
                await asyncio.sleep(pause)  # pause is the delay between sending notes
        else:
            await asyncio.sleep(1)
    
async def main():
    udp_comm = UDPComm('localhost', 8000)
    tcp_comm = TCPComm('localhost', 12346)
    await asyncio.gather(
        send_notes(udp_comm, tcp_comm),
        tcp_comm.check_for_incoming_data(),
    )

if __name__ == "__main__":
    asyncio.run(main())

# async def main(loop):
#     udp_comm = UDPComm('localhost', 8000)
#     tcp_comm = TCPComm('localhost', 12346)
#     await asyncio.gather(
#         tcp_comm.check_for_incoming_data(),
#         send_notes(udp_comm, loop),
#     )

# if __name__ == "__main__":
#     # Get the event loop
#     loop = asyncio.get_event_loop()
#     # Run the main function until it completes
#     loop.run_until_complete(main(loop))

