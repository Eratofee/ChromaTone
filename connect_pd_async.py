import socket
import json
import asyncio
import pandas as pd
import numpy as np
import ast
from drawing import print_trend

PITCH_CLASSES = ["c", "d_b", "d", "e_b", "e", "f", "g_b", "g", "a_b", "a", "b_b", "b"]
oktave = 5
MIDI_MULTIPLIER = oktave * 15

midis = [i for i in range(MIDI_MULTIPLIER, MIDI_MULTIPLIER + len(PITCH_CLASSES))]
translation_pit_2_midi = dict(zip(PITCH_CLASSES, midis))

midi_motives = pd.read_csv("midi_motives.csv")


class PizzaComm:
    def __init__(self, port_name):
        self.output_port_name = port_name

    async def send_midi_note(self, note, velocity, duration):
        pass
        # Send a note on message
        # msg = Message('note_on', note=note, velocity=velocity)
        # self.outport.send(msg)
        # time.sleep(duration)
        # # Send a note off message
        # msg = Message('note_off', note=note, velocity=velocity)
        # self.outport.send(msg)


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
        loop = asyncio.get_running_loop()
        while True:
            try:
                conn, addr = await loop.sock_accept(self.sock)
                print('Connected by', addr)
                data_buffer = b""
                with conn:
                    conn.setblocking(False)
                    while True:
                        try:
                            data = await loop.sock_recv(conn, 1024)
                            if not data:
                                break
                            data_buffer += data
                        except BlockingIOError:
                            await asyncio.sleep(0.1)
                    if data_buffer:
                        received_data = json.loads(data_buffer.decode('utf-8'))
                        self.probabilities = received_data.get("pitch_probabilities")
                        self.trend = received_data.get("trend")
                        self.scale = received_data.get("scale")
                        print("Received data")
                        print("Probabilities:", self.probabilities)
                        print_trend(self.trend)
                        print("Scale:", self.scale)
            except socket.error as e:
                print('Error:', e)
            await asyncio.sleep(0.1)

    def choose_motif(self):
        if self.probabilities:
            key_ind = np.argmax(self.probabilities)
            key = PITCH_CLASSES[key_ind]
            print("Key is", key)
            print_trend(trend=self.trend)
            if self.trend == 4:
                return None
            df_filtered = midi_motives[(midi_motives["direction"] == self.trend) & (midi_motives["scale"] == self.scale)]
            if df_filtered.empty:
                return None
            random_row = df_filtered.sample()
            midi_notes = random_row["midi_notes"].iloc[0]
            return np.array(ast.literal_eval(midi_notes)) + key_ind
        else:
            print("Failed to generate note")
            return None


async def send_notes(pizza_comm, tcp_comm):
    while True:
        notes = tcp_comm.choose_motif()
        if notes is not None:
            for note in notes:
                print(note)
                await asyncio.sleep(2)
                await pizza_comm.send_midi_note(note, 100, 0.5)
        else:
            await asyncio.sleep(1)


async def main():
    pizza_comm = PizzaComm('IAC pizza')
    tcp_comm = TCPComm('localhost', 12346)
    await asyncio.gather(
        tcp_comm.check_for_incoming_data(),
        send_notes(pizza_comm, tcp_comm),
    )


if __name__ == "__main__":
    asyncio.run(main())



# import socket
# import time
# import errno
# import json
# from drawing import print_trend
# import random
# import pandas as pd
# import numpy as np
# import ast
# import asyncio
# import time
# import mido
# from mido import Message, MidiFile, MidiTrack

# pause = .4

# PITCH_CLASSES = ["c", "d_b", "d", "e_b", "e", "f", "g_b","g", "a_b", "a", "b_b", "b"]
# oktave = 5
# MIDI_MULTIPLIER = oktave*15

# midis = [i for i in range(MIDI_MULTIPLIER, MIDI_MULTIPLIER+len(PITCH_CLASSES))]
# translation_pit_2_midi = dict(zip(PITCH_CLASSES, midis))

# # Example note range
# # note_range = list(range(60, 72))  # C4 to B4

# probabilities = None
# trend = None
# scale = 'min'

# midi_motives = pd.read_csv("midi_motives.csv")

# class PizzaComm:
#     def __init__(self, port_name):
#         self.output_port_name = port_name
#         # self.outport = mido.open_output(self.output_port_name)

#     async def send_midi_note(self, note, velocity, duration):
#         pass
#         # Send a note on message
#         # msg = Message('note_on', note=note, velocity=velocity)
#         # self.outport.send(msg)
#         # time.sleep(duration)
#         # # Send a note off message
#         # msg = Message('note_off', note=note, velocity=velocity)
#         # self.outport.send(msg)

# class TCPComm:
#     def __init__(self, ip, port):
#         self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         self.sock.bind((ip, port))
#         self.sock.listen()
#         self.sock.setblocking(False)
#         self.probabilities = None
#         self.trend = None
#         self.scale = 'min'

#     async def check_for_incoming_data(self):
#         loop = asyncio.get_running_loop()
#         while True:
#             print("Inside check_for_incoming_data")
#             try:
#                 conn, addr = await loop.sock_accept(self.sock)
#                 # conn, addr = self.sock.accept()
#                 print('Connected by', addr)
#                 data_buffer = b""
#                 with conn:
#                     conn.setblocking(False)
#                     print("Inside while with conn")
#                     while True:
#                         try:
#                             data = await loop.sock_recv(conn, 1024) 
#                             # data = conn.recv(1024)
#                             if not data:
#                                 break
#                             data_buffer += data
#                         except BlockingIOError:
#                             # If no data is available, yield control and try again later.
#                             await asyncio.sleep(0.1)
#                     if data_buffer:
#                         received_data = json.loads(data_buffer.decode('utf-8'))
#                         self.probabilities = received_data.get("pitch_probabilities")
#                         self.trend = received_data.get("trend")
#                         self.scale = received_data.get("scale")
#                         print("Received data")
#                         print("Probabilities:", self.probabilities)
#                         # print("Trend:", self.trend)
#                         print_trend(self.trend)
#                         print("Scale:", self.scale)
#             except socket.error as e:
#                 print('Error:', e)
#             await asyncio.sleep(0.1)
#             print("End of while loop")

#     def choose_motif(self):
#         if self.probabilities:
#             print("Generating note")
#             key_ind = np.argmax(self.probabilities)
#             key = PITCH_CLASSES[key_ind]
#             print("Key is", key)
#             # print("Trend is", trend)
#             print_trend(trend=self.trend)
#             if trend == 4:
#                 return None
#             df_filtered = midi_motives[(midi_motives["direction"] == self.trend) & (midi_motives["scale"] == self.scale)]
#             random_row = df_filtered.sample()
#             midi_notes = random_row["midi_notes"].iloc[0]
#             return np.array(ast.literal_eval(midi_notes)) + key_ind
#         else:
#             print("Failed to generate note")
#             return None  # Default to random note if no probabilities

# async def send_notes(pizza_comm, tcp_comm):
#     while True:
#         notes = tcp_comm.choose_motif()
#         if notes is not None:
#             for note in notes:
#                 print(note)
#                 await asyncio.sleep(2)
        
#                 # Use the send_note method of the UDPComm instance
#                 await pizza_comm.send_midi_note(note, 100, 0.5)  # Removed loop
#         else:
#             await asyncio.sleep(1)
    
# async def main():
#     pizza_comm = PizzaComm('IAC pizza')
#     tcp_comm = TCPComm('localhost', 12346)
#     await asyncio.gather(
#         tcp_comm.check_for_incoming_data(),
#         send_notes(pizza_comm, tcp_comm),
#     )

# if __name__ == "__main__":
#     asyncio.run(main())
