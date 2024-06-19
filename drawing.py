from tkinter import Button, Canvas, Frame, Tk, ttk, Scale, HORIZONTAL, TRUE, ROUND
from functools import partial
from tkinter.colorchooser import askcolor  # Import the color chooser
from PIL import ImageGrab
import numpy as np
import cv2
import threading
import socket
import json


UP = 0
DOWN = 1
VARYING = 2
CONSTANT = 3
OFF = 4

color_ranges = {
    'red': [(0, 10), (166, 180)],  # Red is split into two ranges [0, 10] and [166, 180
    'orange': (11, 23),
    'yellow': (24, 37),
    'spring_green': (38, 55),
    'green': (56, 68),
    'turquoise': (69, 82),
    'cyan': (83, 99),
    'ocean': (100, 113),
    'blue': (114, 127),
    'violet': (128, 145),
    'magenta': (146, 165)
}

color_notes = {
    "c": "white",
    "d_b": "ocean",
    "d": "turquoise",
    "e_b": "orange",
    "e": "yellow",
    "f": "green",
    "g_b": "spring_green",
    "g": "blue",
    "a_b": "cyan",
    "a": "red",
    "b_b": "magenta",
    "b": "violet"
}

PITCH_CLASSES = ["c", "d_b", "d", "e_b", "e", "f", "g_b","g", "a_b", "a", "b_b", "b"]

def sum_color_counts(color_counts):
    total_count = np.sum(list(color_counts.values()))
    return total_count

def get_color_statistics(image):

    image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

    hue_channel, saturation_channel, value_channel = cv2.split(image)
    
    color_counts = {color: 0 for color in color_ranges}
    color_counts['white'] = 0  # Adding white as a color
    
    black_mask = value_channel < 25
    
    white_mask = np.logical_and(value_channel > 204, saturation_channel < 25)
    color_counts['white'] = np.sum(white_mask)
    
    for color, ranges in color_ranges.items():
        if isinstance(ranges, tuple):
            ranges = [ranges]  
        if color == 'red':
            red1 = np.logical_and(hue_channel >= 0, hue_channel <= 10)
            red2 = np.logical_and(hue_channel >= 166, hue_channel <= 180)
            color_mask = np.logical_or(red1, red2)
            color_mask = np.logical_and(color_mask, np.logical_not(black_mask))
            color_mask = np.logical_and(color_mask, np.logical_not(white_mask))
            color_counts[color] += np.sum(color_mask)
        else:
            for lower_bound, upper_bound in ranges:
                color_mask = np.logical_and(hue_channel >= lower_bound, hue_channel <= upper_bound)
                # Exclude black and white pixels from the color count
                color_mask = np.logical_and(color_mask, np.logical_not(black_mask))
                color_mask = np.logical_and(color_mask, np.logical_not(white_mask))
                
                color_counts[color] += np.sum(color_mask)
            
    temp_total = sum_color_counts(color_counts)

    pitch_probabilities = []
    for pitch in PITCH_CLASSES:
        pitch_probabilities.append(color_counts[color_notes[pitch]]/temp_total)

    return pitch_probabilities

def analyse_send_data(image, trend):
    pitch_probabilities = get_color_statistics(image)

    data_to_send = {
        "pitch_probabilities": pitch_probabilities,
        "trend": trend
    }

    data = json.dumps(data_to_send)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('localhost', 12345))  # Receiver's address and port
        s.sendall(data.encode('utf-8'))

    return 

class DrawingApp:
    def __init__(self, root):
        self.root = root
        self.canvas = Canvas(root, bg='black', width=500, height=500)
        self.canvas.pack()
        self.color = 'black'  # Default color

        self.color_frame = Frame(root)
        self.color_frame.pack()

        self.color_wheel_btn = Button(self.color_frame, text='Choose Color', command=self.choose_color)
        self.color_wheel_btn.pack(side='left')

        # Brush Type Selection
        self.brush_type = ttk.Combobox(self.color_frame, values=["Oval", "Square", "Line"], state="readonly")
        self.brush_type.set("Oval")  # default value
        self.brush_type.pack(side='left')

        # Brush Thickness Selection
        self.brush_thickness_label = ttk.Label(self.color_frame, text="Brush Thickness:")
        self.brush_thickness_label.pack(side='left')
        self.brush_thickness = Scale(self.color_frame, from_=1, to=10, orient=HORIZONTAL)
        self.brush_thickness.set(2)  # default thickness
        self.brush_thickness.pack(side='left')

        self.last_pos = None 
        self.directions = []
        self.trend = OFF
        self.canvas.bind('<B1-Motion>', self.paint)
        self.canvas.bind('<ButtonRelease-1>', self.reset_last_pos)  # Reset last_pos on mouse release
        self.capture_delay = 5000  # Delay in milliseconds between captures
        self.capture_canvas_content()

    def choose_color(self):
        color_code = askcolor(title="Choose color")[1]
        if color_code:
            self.color = color_code

    def analyze_trend(self):
        up_count = self.directions.count(UP)
        down_count = self.directions.count(DOWN)
        constant_count = self.directions.count(CONSTANT)
        dir_len = len(self.directions)

        if abs(up_count - down_count) < 10 and constant_count < 10:
            return VARYING
        if up_count > dir_len / 2:
            return UP
        elif down_count > dir_len / 2:
            return DOWN
        elif constant_count > dir_len / 2:
            return CONSTANT
        else:
            return VARYING
        
    def print_trend(self):
        if self.trend == UP:
            print("Trend: Up")
        elif self.trend == DOWN:
            print("Trend: Down")
        elif self.trend == CONSTANT:
            print("Trend: Constant")
        elif self.trend == VARYING:
            print("Trend: Varying")
        else:
            print("Trend: Off")

    def paint(self, event):
        x, y = event.x, event.y
        size = self.brush_thickness.get()
        if self.brush_type.get() == "Oval":
            self.canvas.create_oval(x-size, y-size, x+size, y+size, fill=self.color, outline=self.color)
        elif self.brush_type.get() == "Square":
            self.canvas.create_rectangle(x-size, y-size, x+size, y+size, fill=self.color, outline=self.color)
        elif self.brush_type.get() == "Line" and self.last_pos:
            self.canvas.create_line(self.last_pos[0], self.last_pos[1], x, y, fill=self.color, width=size, capstyle=ROUND, smooth=TRUE, splinesteps=36)
        
        if self.last_pos:
            dx = x - self.last_pos[0]
            dy = y - self.last_pos[1]
            
            if dy < 0:
                direction = UP
            elif dy > 0:
                direction = DOWN
            else:
                direction = CONSTANT
            
            # print("Direction:", self.print_trend(direction)) 

            self.directions.append(direction)
            if len(self.directions) > 100:
                self.trend = self.analyze_trend()
                self.directions = []
                # self.directions.pop(0)
                self.print_trend()

        self.last_pos = (x, y)  

    def reset_last_pos(self, event):
        self.last_pos = None  
        self.trend = OFF
        self.print_trend()

    def capture_canvas_content(self):
        def capture_and_analyze():
            x = self.root.winfo_rootx() + self.canvas.winfo_x()
            y = self.root.winfo_rooty() + self.canvas.winfo_y()
            x1 = x + self.canvas.winfo_width()
            y1 = y + self.canvas.winfo_height()
            image = ImageGrab.grab(bbox=(x, y, x1, y1))
            
            analyse_send_data(np.array(image))

        analysis_thread = threading.Thread(target=capture_and_analyze)
        analysis_thread.start()
        # capture_and_analyze()
        self.root.after(self.capture_delay, self.capture_canvas_content)

def main():
    root = Tk()
    app = DrawingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()