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
import colorutils

from utils import UP, DOWN, VARYING, CONSTANT, OFF, color_ranges, color_notes, notes_colors, PITCH_CLASSES, print_trend

def sum_color_counts(color_counts):
    total_count = np.sum(list(color_counts.values()))
    return total_count

def calculate_color_mask(hue_channel, color_ranges, black_mask, white_mask):
    color_counts = {color: 0 for color in color_ranges}
    color_counts['white'] = np.sum(white_mask)

    for color, ranges in color_ranges.items():
        if isinstance(ranges, tuple):
            ranges = [ranges]
        if color == 'red':
            red1 = np.logical_and(hue_channel >= 0, hue_channel <= 10)
            red2 = np.logical_and(hue_channel >= 166, hue_channel <= 180)
            color_mask = np.logical_or(red1, red2)
        else:
            color_mask = np.zeros_like(hue_channel, dtype=bool)
            for lower_bound, upper_bound in ranges:
                color_mask |= np.logical_and(hue_channel >= lower_bound, hue_channel <= upper_bound)

        color_mask = np.logical_and(color_mask, np.logical_not(black_mask))
        color_mask = np.logical_and(color_mask, np.logical_not(white_mask))
        color_counts[color] += np.sum(color_mask)

    return color_counts

def calculate_pitch_probabilities(color_counts, color_notes):
    temp_total = sum(color_counts.values())
    pitch_probabilities = [color_counts[color_notes[pitch]] / temp_total for pitch in PITCH_CLASSES]
    return pitch_probabilities

def get_color_statistics(image):
    image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    hue_channel, saturation_channel, value_channel = cv2.split(image)
    average_brightness = np.mean(value_channel)

    scale = 'min' if average_brightness < 127 else 'maj'

    black_mask = value_channel < 25
    white_mask = np.logical_and(value_channel > 204, saturation_channel < 25)

    color_counts = calculate_color_mask(hue_channel, color_ranges, black_mask, white_mask)
    pitch_probabilities = calculate_pitch_probabilities(color_counts, color_notes)

    return pitch_probabilities, scale

def determine_color(hue, saturation, value):
    if value < 25:
        return None
    elif value > 204 and saturation < 25:
        return 'white'
    else:
        for color, ranges in color_ranges.items():
            if isinstance(ranges, tuple):
                ranges = [ranges]
            if color == 'red':
                if (hue >= 0 and hue <= 10) or (hue >= 166 and hue <= 180):
                    return color
            else:
                for lower_bound, upper_bound in ranges:
                    if hue >= lower_bound and hue <= upper_bound:
                        return color
    return None

def active_color_probabilities(active_color):
    hsv_color = colorutils.hex_to_hsv(active_color)
    hue = hsv_color[0] / 2
    saturation = hsv_color[1] * 255
    value = hsv_color[2] * 255

    color_str = determine_color(hue, saturation, value)
    return notes_colors[color_str] if color_str else None


def analyse_send_data(image, trend, speed_measure, active_color_flag, active_color):
    key = None
    if active_color_flag:
        key = active_color_probabilities(active_color)
        if key == None:
            active_color_flag = False

    pitch_probabilities, scale = get_color_statistics(image)

    if speed_measure > 7000:
        duration = 0.01
    elif speed_measure > 5000:
        duration = 0.05
    elif speed_measure > 3000:
        duration = 0.1
    elif speed_measure > 1000:
        duration = 0.15
    elif speed_measure > 500:
        duration = 0.25
    elif speed_measure > 100:
        duration = 0.3
    else:
        duration = 0.35

    print("Pitch Probabilities:", pitch_probabilities)
    print_trend(trend)
    print("Scale:", scale)
    print("Duration:", duration)

    data_to_send = {
        "pitch_probabilities": pitch_probabilities,
        "scale": scale,
        "trend": trend,
        "duration": duration,
        "active_color_flag": active_color_flag,
        "key": key,
    }

    data = json.dumps(data_to_send)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('localhost', 12346))  
        s.sendall(data.encode('utf-8'))
    return 

class DrawingApp:
    def __init__(self, root):
        self.initialize_basic_attributes(root)
        self.configure_style()
        self.setup_ui_components()
        self.bind_canvas_events()
        self.initialize_other_attributes()
        self.capture_canvas_content()

    def initialize_basic_attributes(self, root):
        self.root = root
        root.title('ChromaTone')

    def configure_style(self):
        self.style = ttk.Style()
        self.style.theme_use('default')  
        self.style.configure("Horizontal.TScale", background='#333', foreground='white', troughcolor='#555', sliderlength=20, borderwidth=1)
        self.style.map("Horizontal.TScale", background=[('active', '#555')])
        self.style.configure("Eraser.TButton", font=('Helvetica', 13))
        self.style.configure("ActiveEraser.TButton", font=('Helvetica', 13, 'bold'))

    def setup_ui_components(self):
        self.setup_color_frame()
        self.setup_color_wheel()
        self.setup_brush_type_selection()
        self.setup_eraser_button()
        self.setup_active_color_button()
        self.setup_brush_thickness_selection()
        self.setup_canvas()

    def setup_color_frame(self):
        self.color_frame = Frame(self.root)
        self.color_frame.pack(side='top', fill='x', padx=10, pady=5)

    def setup_color_wheel(self):
        self.color_wheel_btn = ttk.Button(self.color_frame, text='Choose Color', command=self.choose_color)
        self.color_wheel_btn.pack(side='left', padx=5, in_=self.color_frame)

    def setup_brush_type_selection(self):
        self.brush_type = ttk.Combobox(self.color_frame, values=[ "Line", "Oval", "Square"], state="readonly")
        self.brush_type.set("Line") 
        self.brush_type.pack(side='left', padx=5, in_=self.color_frame)

    def setup_eraser_button(self):
        self.eraser_btn = ttk.Button(self.root, text='Eraser', style="Eraser.TButton", command=self.toggle_eraser)
        self.eraser_btn.pack(side='left', padx=5, in_=self.color_frame)

    def setup_active_color_button(self):
        self.active_color_btn = ttk.Button(self.root, text='Active Color', style="Eraser.TButton", command=self.toggle_active_color)
        self.active_color_btn.pack(side='left', padx=5, in_=self.color_frame)

    def setup_brush_thickness_selection(self):
        self.brush_thickness_label = ttk.Label(self.color_frame, text="Thickness:")
        self.brush_thickness_label.pack(side='left', padx=5, in_=self.color_frame)
        self.brush_thickness = ttk.Scale(self.color_frame, from_=1, to=40, orient='horizontal', style="Horizontal.TScale")
        self.brush_thickness.set(10)  # default thickness
        self.brush_thickness.pack(side='left', padx=5, in_=self.color_frame)

    def setup_canvas(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.canvas = Canvas(self.root, bg='black', width=screen_width, height=screen_height - self.color_frame.winfo_reqheight())
        self.canvas.pack(padx=10, pady=5)

    def bind_canvas_events(self):
        self.canvas.bind('<B1-Motion>', self.paint)
        self.canvas.bind('<ButtonRelease-1>', self.reset_last_pos)

    def initialize_other_attributes(self):
        self.color = '#FFFFFF'
        self.active_color_flag = False
        self.last_pos = None 
        self.directions = []
        self.speeds = []
        self.speed_measure = 0
        self.trend = CONSTANT
        self.eraser_active = False
        self.direction_speed_analysis_limit = 100
        self.capture_delay = 2000  

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

    def toggle_active_color(self):
        self.active_color_flag = not self.active_color_flag
        if self.active_color_flag:
            self.active_color_btn.configure(style="ActiveEraser.TButton")
        else:
            self.active_color_btn.configure(style="Eraser.TButton")

    def paint(self, event):
        paint_color = self.determine_paint_color()
        current_time = time.time()
        self.calculate_speed(current_time, event)
        self.draw_shape(event, paint_color)
        self.analyze_direction_and_speed(event)
        self.update_position_and_time(event, current_time)

    def determine_paint_color(self):
        return '#000000' if self.eraser_active else self.color

    def calculate_speed(self, current_time, event):
        if hasattr(self, 'last_time') and self.last_pos is not None:
            time_diff = current_time - self.last_time
            distance = math.sqrt((event.x - self.last_pos[0])**2 + (event.y - self.last_pos[1])**2)
            if time_diff > 0:
                speed_measure = distance / time_diff
                self.speeds.append(speed_measure)

    def draw_shape(self, event, paint_color):
        x, y = event.x, event.y
        size = self.brush_thickness.get()
        if self.brush_type.get() == "Oval":
            self.canvas.create_oval(x-size, y-size, x+size, y+size, fill=paint_color, outline=paint_color)
        elif self.brush_type.get() == "Square":
            self.canvas.create_rectangle(x-size, y-size, x+size, y+size, fill=paint_color, outline=paint_color)
        elif self.brush_type.get() == "Line" and self.last_pos:
            self.canvas.create_line(self.last_pos[0], self.last_pos[1], x, y, fill=paint_color, width=size, capstyle=ROUND, smooth=TRUE, splinesteps=36)

    def analyze_direction_and_speed(self, event):
        if not self.eraser_active and self.last_pos:
            dy = event.y - self.last_pos[1]
            if dy < 0:
                direction = UP
            elif dy > 0:
                direction = DOWN
            else:
                direction = CONSTANT

            self.directions.append(direction)
            if len(self.directions) > self.direction_speed_analysis_limit:
                self.trend = self.analyze_trend()
                self.speed_measure = np.mean(self.speeds)
                self.directions = []
                self.speeds = []

    def update_position_and_time(self, event, current_time):
        self.last_pos = (event.x, event.y)
        self.last_time = current_time

    def reset_last_pos(self, event):
        self.last_pos = None

    def capture(self):
        x = self.root.winfo_rootx() + self.canvas.winfo_x()
        y = self.root.winfo_rooty() + self.canvas.winfo_y()
        x1 = x + self.canvas.winfo_width()
        y1 = y + self.canvas.winfo_height()
        return ImageGrab.grab(bbox=(x, y, x1, y1))

    def analyze(self, image):
        try:
            analyse_send_data(np.array(image), self.trend, self.speed_measure, self.active_color_flag, self.color)
        except Exception as e:
            print(f"Error during analysis: {e}")

    def capture_and_analyze(self):
        image = self.capture()
        self.analyze(image)

    def capture_canvas_content(self):
        analysis_thread = threading.Thread(target=self.capture_and_analyze)
        analysis_thread.start()
        self.root.after(self.capture_delay, self.capture_canvas_content)

def main():
    root = Tk()
    app = DrawingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()