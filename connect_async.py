import socket
import json
import asyncio
import numpy as np
import mido
import time
from mido import Message
from motifs_gen import MotifGen

class PizzaComm:
    def __init__(self, port_name_harp, port_name_drone):
        # Initialize MIDI output ports for harp and drone
        self.output_port_name_harp = port_name_harp
        self.output_port_name_drone = port_name_drone
        self.outport_harp = mido.open_output(self.output_port_name_harp)
        self.outport_drone = mido.open_output(self.output_port_name_drone)

    async def send_midi_note(self, note, velocity, duration):
        # Send a note on message for harp
        msg = Message('note_on', note=note, velocity=velocity)
        self.outport_harp.send(msg)
        time.sleep(duration)
        # Send a note off message for harp
        msg = Message('note_off', note=note, velocity=velocity)
        self.outport_harp.send(msg)

    async def send_midi_note_on(self, note, velocity):
        # Send a note on message for drone
        msg = Message('note_on', note=note, velocity=velocity)
        self.outport_drone.send(msg)

    async def send_midi_note_off(self, note, velocity):
        # Send a note off message for drone
        msg = Message('note_off', note=note, velocity=velocity)
        self.outport_drone.send(msg)

class TCPComm:
    def __init__(self, ip, port):
        # Initialize a TCP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((ip, port))
        self.sock.listen()
        self.sock.setblocking(False)

    async def check_for_incoming_data(self, motif_gen):
        loop = asyncio.get_running_loop()
        while True:
            try:
                # Accept a new connection
                conn, addr = await loop.sock_accept(self.sock)
                print('Connected by', addr)
                data_buffer = b""
                with conn:
                    conn.setblocking(False)
                    while True:
                        try:
                            # Receive data in chunks
                            data = await loop.sock_recv(conn, 1024)
                            if not data:
                                break
                            data_buffer += data
                        except BlockingIOError:
                            await asyncio.sleep(0.1)
                    if data_buffer:
                        # Decode and process the received JSON data
                        received_data = json.loads(data_buffer.decode('utf-8'))
                        probabilities = received_data.get("pitch_probabilities")
                        trend = received_data.get("trend")
                        scale = received_data.get("scale")
                        duration = received_data.get("duration")
                        active_color_flag = received_data.get("active_color_flag")
                        if active_color_flag:
                            key = received_data.get("key")
                            motif_gen.set_key(key)
                        motif_gen.set_active_color_flag(active_color_flag)
                        motif_gen.set_probabilities(probabilities)
                        motif_gen.set_trend(trend)
                        motif_gen.set_scale(scale)
                        motif_gen.set_duration(duration)
                        print("Received data")
                        print("Duration:", duration)
            except socket.error as e:
                print('Error:', e)
            await asyncio.sleep(0.1)

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
                if duration_changed(duration):
                    print("duration changed")
                    duration = motif_gen.get_duration()
            await pizza_comm.send_midi_note_off(key, 70)
        else:
            print("no notes, waiting")
            await asyncio.sleep(1)

async def main():
    # Initialize communication objects
    pizza_comm = PizzaComm('IAC pizza', 'IAC drone')
    tcp_comm = TCPComm('localhost', 12346)
    motif_gen = MotifGen(with_markov=True)
    # Start tasks for checking incoming data and sending notes
    await asyncio.gather(
        tcp_comm.check_for_incoming_data(motif_gen),
        send_notes(pizza_comm, motif_gen),
    )

if __name__ == "__main__":
    # Run the main event loop
    asyncio.run(main())
