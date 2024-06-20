from tkinter import Canvas, Frame, Tk, ttk, Button, font, HORIZONTAL, TRUE, ROUND, RAISED, SUNKEN
from functools import partial
from tkinter.colorchooser import askcolor 
from PIL import ImageGrab
import numpy as np
import cv2
import threading
import socket
import json
import time
import math

UP = 0
DOWN = 1
VARYING = 2
CONSTANT = 3
OFF = 4

color_ranges = {
    'red': [(0, 10), (166, 180)], 
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
    
    average_brightness = np.mean(value_channel)

    scale = 'min'
    if average_brightness < 127:
        scale = 'min'
    else:
        scale = 'maj'

    color_counts = {color: 0 for color in color_ranges}   
    color_counts['white'] = 0  
    
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

    return pitch_probabilities, scale

def print_trend(trend):
    if trend == UP:
        print("Trend: Up")
    elif trend == DOWN:
        print("Trend: Down")
    elif trend == CONSTANT:
        print("Trend: Constant")
    elif trend == VARYING:
        print("Trend: Varying")
    else:
        print("Trend: Off")


def analyse_send_data(image, trend, speed_measure):
    pitch_probabilities, scale = get_color_statistics(image)

    if speed_measure > 7000:
        duration = 0.1
    elif speed_measure > 5000:
        duration = 0.25
    elif speed_measure > 3000:
        duration = 0.4
    elif speed_measure > 1000:
        duration = 0.8
    elif speed_measure > 500:
        duration = 1
    else:
        duration = 2

    print("Pitch Probabilities:", pitch_probabilities)
    print_trend(trend)
    print("Scale:", scale)
    print("Duration:", duration)

    data_to_send = {
        "pitch_probabilities": pitch_probabilities,
        "scale": scale,
        "trend": trend,
        "duration": duration
    }

    data = json.dumps(data_to_send)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('localhost', 12346))  
        s.sendall(data.encode('utf-8'))

    return 

class DrawingApp:
    def __init__(self, root):
        self.root = root
        self.last_pos = (0, 0)
        root.title('ChromaTone')
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # Apply a theme
        self.style = ttk.Style()
        self.style.theme_use('default')  
        self.style.configure("Horizontal.TScale", background='#333', foreground='white', troughcolor='#555', sliderlength=20, borderwidth=1)
        self.style.map("Horizontal.TScale", background=[('active', '#555')])
        self.style.configure("Eraser.TButton", font=('Helvetica', 13))
        self.style.configure("ActiveEraser.TButton", font=('Helvetica', 13, 'bold'))

        self.color_frame = Frame(root)
        self.color_frame.pack(side='top', fill='x', padx=10, pady=5)


        self.color_wheel_btn = ttk.Button(self.color_frame, text='Choose Color', command=self.choose_color)
        self.color_wheel_btn.pack(side='left', padx=5, in_=self.color_frame)

        # Brush Type Selection
        self.brush_type = ttk.Combobox(self.color_frame, values=[ "Line", "Oval", "Square"], state="readonly")
        self.brush_type.set("Line") 
        self.brush_type.pack(side='left', padx=5, in_=self.color_frame)

        # Eraser Button
        self.eraser_btn = ttk.Button(self.root, text='Eraser', style="Eraser.TButton", command=self.toggle_eraser)
        self.eraser_btn.pack(side='left', padx=5, in_=self.color_frame)

        # Brush Thickness Selection
        self.brush_thickness_label = ttk.Label(self.color_frame, text="Thickness:")
        self.brush_thickness_label.pack(side='left', padx=5, in_=self.color_frame)
        self.brush_thickness = ttk.Scale(self.color_frame, from_=1, to=40, orient='horizontal', style="Horizontal.TScale")
        self.brush_thickness.set(10)  # default thickness
        self.brush_thickness.pack(side='left', padx=5, in_=self.color_frame)

        self.canvas = Canvas(root, bg='black', width=screen_width, height=screen_height - self.color_frame.winfo_reqheight())
        self.canvas.pack(padx=10, pady=5)
        self.color = 'white'

        self.last_pos = None 
        self.directions = []
        self.speeds = []
        self.speed_measure = 0
        self.trend = CONSTANT
        self.eraser_active = False
        self.canvas.bind('<B1-Motion>', self.paint)
        self.canvas.bind('<ButtonRelease-1>', self.reset_last_pos) 
        self.capture_delay = 2000  
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
        elif up_count > dir_len / 2:
            return UP
        elif down_count > dir_len / 2:
            return DOWN
        elif constant_count > dir_len / 2:
            return CONSTANT
        else:
            return VARYING

    def toggle_eraser(self):
        self.eraser_active = not self.eraser_active
        
        if self.eraser_active:
            self.eraser_btn.configure(style="ActiveEraser.TButton")
        else:
            self.eraser_btn.configure(style="Eraser.TButton")

    def paint(self, event):
        paint_color = 'black' if self.eraser_active else self.color
        current_time = time.time()

        if hasattr(self, 'last_time'):
            if self.last_pos != None:
                time_diff = current_time - self.last_time
                distance = math.sqrt((event.x - self.last_pos[0])**2 + (event.y - self.last_pos[1])**2)
                
                # Avoid division by zero
                if time_diff > 0:
                    speed_measure = distance / time_diff
                    # Invert the speed measure to match the requested behavior
                    # speed_measure = 1 / speed if speed != 0 else float('inf')
                    self.speeds.append(speed_measure)
                    # print("Speed Measure:", speed_measure)
                # else:
                    # print("Time difference is too small.")
            # else:
                # print("First paint event, no speed measure.")
    
        x, y = event.x, event.y
        size = self.brush_thickness.get()
        if self.brush_type.get() == "Oval":
            self.canvas.create_oval(x-size, y-size, x+size, y+size, fill=paint_color, outline=paint_color)
        elif self.brush_type.get() == "Square":
            self.canvas.create_rectangle(x-size, y-size, x+size, y+size, fill=paint_color, outline=paint_color)
        elif self.brush_type.get() == "Line" and self.last_pos:
            self.canvas.create_line(self.last_pos[0], self.last_pos[1], x, y, fill=paint_color, width=size, capstyle=ROUND, smooth=TRUE, splinesteps=36)
        
        if not self.eraser_active:
            if self.last_pos:
                # dx = x - self.last_pos[0]
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
                    self.speed_measure = np.mean(self.speeds)
                    print("Speed: ", self.speed_measure)
                    self.directions = []
                    self.speeds = []
                    # self.directions.pop(0)
                    # print_trend(self.trend)

        self.last_pos = (x, y)
        self.last_time = current_time

    def reset_last_pos(self, event):
        self.last_pos = None  
        # self.trend = OFF
        # print_trend(self.trend)

    def capture_canvas_content(self):
        def capture_and_analyze():
            x = self.root.winfo_rootx() + self.canvas.winfo_x()
            y = self.root.winfo_rooty() + self.canvas.winfo_y()
            x1 = x + self.canvas.winfo_width()
            y1 = y + self.canvas.winfo_height()
            image = ImageGrab.grab(bbox=(x, y, x1, y1))
            
            analyse_send_data(np.array(image), self.trend, self.speed_measure)

        analysis_thread = threading.Thread(target=capture_and_analyze)
        analysis_thread.start()
        self.root.after(self.capture_delay, self.capture_canvas_content)

def main():
    root = Tk()
    app = DrawingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()