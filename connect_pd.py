import socket
import time

UDP_IP = "127.0.0.1"  # Localhost (adjust if Pd is on a different machine)
UDP_PORT = 8000   

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

pause=.5
         
notes = [(60, 0), (61, 1), (62, 1), (0,0)]

for note in notes:
    # Convert the tuple to bytes
    note_bytes = note[0].to_bytes(1, 'big') + note[1].to_bytes(1, 'big')
    
    # Send the bytes over UDP
    sock.sendto(note_bytes, (UDP_IP, UDP_PORT))
    
    # Pause
    time.sleep(pause)