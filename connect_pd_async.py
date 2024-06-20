import socket
import json
import asyncio
import pandas as pd
import numpy as np
import ast
from drawing import print_trend
import mido
from mido import Message, MidiFile, MidiTrack
import time

UP = 0
DOWN = 1
VARYING = 2
CONSTANT = 3
OFF = 4

PITCH_CLASSES = ["c", "d_b", "d", "e_b", "e", "f", "g_b", "g", "a_b", "a", "b_b", "b"]
oktave = 5
MIDI_MULTIPLIER = oktave * 15

midis = [i for i in range(MIDI_MULTIPLIER, MIDI_MULTIPLIER + len(PITCH_CLASSES))]
translation_pit_2_midi = dict(zip(PITCH_CLASSES, midis))
midi_motives = pd.read_csv("midi_motives.csv")


class PizzaComm:
    def __init__(self, port_name):
        self.output_port_name = port_name
        self.outport = mido.open_output(self.output_port_name)

    async def send_midi_note(self, note, velocity, duration):
        # Send a note on message
        msg = Message('note_on', note=note, velocity=velocity)
        self.outport.send(msg)
        time.sleep(duration)
        # Send a note off message
        msg = Message('note_off', note=note, velocity=velocity)
        self.outport.send(msg)

    async def send_midi_note_on(self, note, velocity):
        msg = Message('note_on', note=note, velocity=velocity)
        self.outport.send(msg)

    async def send_midi_note_off(self, note, velocity):
        msg = Message('note_off', note=note, velocity=velocity)
        self.outport.send(msg)

class TCPComm:
    def __init__(self, ip, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((ip, port))
        self.sock.listen()
        self.sock.setblocking(False)
        # self.probabilities = None
        # self.trend = None
        # self.scale = 'min'

    async def check_for_incoming_data(self, motif_gen):
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
                        probabilities = received_data.get("pitch_probabilities")
                        trend = received_data.get("trend")
                        scale = received_data.get("scale")
                        duration = received_data.get("duration")
                        motif_gen.set_probabilities(probabilities)
                        motif_gen.set_trend(trend)
                        motif_gen.set_scale(scale)
                        motif_gen.set_duration(duration)
                        print("Received data")
                        # print("Probabilities:", probabilities)
                        # print_trend(trend)
                        # print("Scale:", scale)
                        print("Duration:", duration)
            except socket.error as e:
                print('Error:', e)
            await asyncio.sleep(0.1)

class MotifGen:
    def __init__(self):
        self.probabilities = None
        self.scale = None
        self.trend = CONSTANT
        self.duration = 0.5

    def set_probabilities(self, probabilities):
        self.probabilities = probabilities

    def set_trend(self, trend):
        self.trend = trend

    def set_scale(self, scale):
        self.scale = scale

    def set_duration(self, duration):
        self.duration = duration

    def get_trend(self):
        return self.trend
    
    def get_duration(self):
        return self.duration

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
            return np.array(ast.literal_eval(midi_notes)) + key_ind, self.duration, self.trend, translation_pit_2_midi[key] - 24
        else:
            print("Failed to generate note")
            return None, None, None, None


async def send_notes(pizza_comm, motif_gen):
    def duration_changed(duration):
        return motif_gen.get_duration() != duration
    
    def trend_changed(trend):
        return motif_gen.get_trend() != trend

    while True:
        print("Choosing motif")
        notes, duration, trend, key = motif_gen.choose_motif()
        print("Key: ", key)
        if notes is not None and duration is not None:
            await pizza_comm.send_midi_note_on(key, 100)
            for note in notes:
                print(note)
                await asyncio.sleep(0.1)
                vel = np.random.randint(60, 100)
                await pizza_comm.send_midi_note(note, vel, duration)
                if trend_changed(trend):
                    print("trend changed")
                    break
                elif duration_changed(duration):
                    print("duration changed")
                    duration = motif_gen.get_duration()

            await pizza_comm.send_midi_note_off(key, 70)
        else:
            print("no notes, waiting")
            await asyncio.sleep(1)


async def main():
    pizza_comm = PizzaComm('IAC pizza')
    tcp_comm = TCPComm('localhost', 12346)
    motif_gen = MotifGen()
    await asyncio.gather(
        tcp_comm.check_for_incoming_data(motif_gen),
        send_notes(pizza_comm, motif_gen),
    )


if __name__ == "__main__":
    asyncio.run(main())
