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
    """
    Calculates the total count of all colors.
    
    Parameters:
        color_counts (dict): A dictionary where keys are color names and values are counts of those colors.
    
    Returns:
        int: The total count of all colors.
    """
    total_count = np.sum(list(color_counts.values()))
    return total_count

def calculate_color_mask(hue_channel, color_ranges, black_mask, white_mask):
    """
    Calculates the mask for each color in the image based on hue values, excluding black and white areas.
    
    Parameters:
        hue_channel (numpy.ndarray): The hue channel of the image.
        color_ranges (dict): A dictionary defining the hue ranges for each color.
        black_mask (numpy.ndarray): A mask indicating black areas in the image.
        white_mask (numpy.ndarray): A mask indicating white areas in the image.
    
    Returns:
        dict: A dictionary with color names as keys and their respective counts as values.
    """
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
    """
    Calculates the probabilities of each pitch class based on color counts.
    
    Parameters:
        color_counts (dict): A dictionary with color names as keys and their respective counts as values.
        color_notes (dict): A dictionary mapping color names to musical notes.
    
    Returns:
        list: A list of probabilities for each pitch class.
    """
    temp_total = sum(color_counts.values())
    pitch_probabilities = [color_counts[color_notes[pitch]] / temp_total for pitch in PITCH_CLASSES]
    return pitch_probabilities

def get_color_statistics(image):
    """
    Analyzes an image to determine pitch probabilities and musical scale based on color distribution.
    
    Parameters:
        image (numpy.ndarray): The image to analyze.
    
    Returns:
        tuple: A tuple containing a list of pitch probabilities and the determined musical scale ('min' or 'maj').
    """
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
    """
    Determines the color based on hue, saturation, and value.
    
    Parameters:
        hue (float): The hue value of the color.
        saturation (float): The saturation value of the color.
        value (float): The brightness value of the color.
    
    Returns:
        str or None: The determined color as a string, or None if no color matches.
    """
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
    """
    Determines the note probabilities based on an active color.
    
    Parameters:
        active_color (str): The active color in hexadecimal format.
    
    Returns:
        dict or None: A dictionary with note probabilities if the color is recognized, otherwise None.
    """
    hsv_color = colorutils.hex_to_hsv(active_color)
    hue = hsv_color[0] / 2
    saturation = hsv_color[1] * 255
    value = hsv_color[2] * 255

    color_str = determine_color(hue, saturation, value)
    return notes_colors[color_str] if color_str else None

def analyse_send_data(image, trend, speed_measure, active_color_flag, active_color):
    """
    Analyzes an image and sends the data over a network socket.
    
    Parameters:
        image (numpy.ndarray): The image to analyze.
        trend (str): The current trend in drawing movement.
        speed_measure (int): The speed of the drawing action.
        active_color_flag (bool): Flag indicating if an active color is used.
        active_color (str): The active color in hexadecimal format.
    """
    key = active_color_probabilities(active_color) if active_color_flag else None
    active_color_flag = bool(key)

    pitch_probabilities, scale = get_color_statistics(image)

    duration = calculate_duration(speed_measure)

    print_analysis_results(pitch_probabilities, trend, scale, duration)

    data_to_send = {
        "pitch_probabilities": pitch_probabilities,
        "scale": scale,
        "trend": trend,
        "duration": duration,
        "active_color_flag": active_color_flag,
        "key": key,
    }

    send_data(json.dumps(data_to_send))

def calculate_duration(speed_measure):
    """
    Determines the duration of a note based on the speed of drawing.
    
    Parameters:
        speed_measure: The speed of the drawing action, calculated as distance over time.
    
    Returns:
        A float representing the duration of the note, with faster speeds resulting in shorter durations.
    """
    if speed_measure > 7000:
        return 0.01
    elif speed_measure > 5000:
        return 0.05
    elif speed_measure > 3000:
        return 0.1
    elif speed_measure > 1000:
        return 0.15
    elif speed_measure > 500:
        return 0.25
    elif speed_measure > 100:
        return 0.3
    else:
        return 0.35

def print_analysis_results(pitch_probabilities, trend, scale, duration):
    """
    Prints the analysis results including pitch probabilities, drawing trend, scale, and note duration.
    
    Parameters:
        pitch_probabilities: A list of probabilities for different pitches based on the analysis.
        trend: The general direction of the drawing movement (up, down, constant).
        scale: The musical scale determined from the analysis.
        duration: The duration of the note, influenced by the speed of drawing.
    """
    print("Drawing App:")
    print("Pitch Probabilities:", pitch_probabilities)
    print_trend(trend)
    print("Scale:", scale)
    print("Duration:", duration)

def send_data(data):
    """
    Sends the serialized analysis data over a network socket to a predefined address and port.
    
    Parameters:
        data: The serialized (JSON) string containing the analysis results to be sent.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('localhost', 12346))
        s.sendall(data.encode('utf-8'))


class DrawingApp:
    """
    A GUI application for drawing and painting, built with Tkinter.
    
    Attributes:
        root (Tk): The main window of the application.
        style (ttk.Style): The style configuration for the Tkinter widgets.
        color_frame (Frame): The frame that holds color selection and brush options.
        color_wheel_btn (ttk.Button): Button to open the color wheel for color selection.
        brush_type (ttk.Combobox): Dropdown to select the type of brush for drawing.
        eraser_btn (ttk.Button): Button to toggle eraser mode.
        active_color_btn (ttk.Button): Button to toggle the active drawing color.
        brush_thickness_label (ttk.Label): Label for the brush thickness scale.
        brush_thickness (ttk.Scale): Scale to select the thickness of the brush.
        canvas (Canvas): The main drawing canvas.
        color (str): The current active color for drawing.
        active_color_flag (bool): Flag to indicate if the active color is selected.
        last_pos (tuple): The last recorded position of the mouse cursor.
        directions (list): A list to track the direction of drawing movements.
        speeds (list): A list to track the speed of drawing movements.
        speed_measure (int): A measure of the current drawing speed.
        trend (str): The current trend in drawing direction or speed.
        eraser_active (bool): Flag to indicate if the eraser mode is active.
        direction_speed_analysis_limit (int): The limit for analyzing direction and speed data.
        capture_delay (int): The delay in milliseconds for capturing canvas content.
    """
    def __init__(self, root):
        """
        Initializes the DrawingApp with a root window and sets up the UI components.
        
        Parameters:
            root (Tk): The main window of the application.
        """
        self.initialize_basic_attributes(root)
        self.configure_style()
        self.setup_ui_components()
        self.bind_canvas_events()
        self.initialize_other_attributes()
        self.capture_canvas_content()

    def initialize_basic_attributes(self, root):
        """
        Initializes the basic attributes of the application.
        
        Parameters:
            root (Tk): The main window of the application.
        """
        self.root = root
        root.title('ChromaTone')

    def configure_style(self):
        """
        Configures the style of the Tkinter widgets used in the application.
        """
        self.style = ttk.Style()
        self.style.theme_use('default')  
        self.style.configure("Horizontal.TScale", background='#333', foreground='white', troughcolor='#555', sliderlength=20, borderwidth=1)
        self.style.map("Horizontal.TScale", background=[('active', '#555')])
        self.style.configure("Eraser.TButton", font=('Helvetica', 13))
        self.style.configure("ActiveEraser.TButton", font=('Helvetica', 13, 'bold'))

    def setup_ui_components(self):
        """
        Sets up the UI components of the application.
        """
        self.setup_color_frame()
        self.setup_color_wheel()
        self.setup_brush_type_selection()
        self.setup_eraser_button()
        self.setup_active_color_button()
        self.setup_brush_thickness_selection()
        self.setup_canvas()

    def setup_color_frame(self):
        """
        Sets up the frame for color selection tools in the application.
        This frame is positioned at the top of the application window and contains
        elements related to color selection such as the color wheel button.
        """
        self.color_frame = Frame(self.root)
        self.color_frame.pack(side='top', fill='x', padx=10, pady=5)

    def setup_color_wheel(self):
        """
        Adds a button to the color frame that opens a color chooser dialog when clicked.
        This allows the user to select a color for drawing.
        """
        self.color_wheel_btn = ttk.Button(self.color_frame, text='Choose Color', command=self.choose_color)
        self.color_wheel_btn.pack(side='left', padx=5, in_=self.color_frame)

    def setup_brush_type_selection(self):
        """
        Adds a dropdown menu to the color frame for selecting the brush type.
        The available options are "Line", "Oval", and "Square". The default selection is "Line".
        """
        self.brush_type = ttk.Combobox(self.color_frame, values=[ "Line", "Oval", "Square"], state="readonly")
        self.brush_type.set("Line") 
        self.brush_type.pack(side='left', padx=5, in_=self.color_frame)

    def setup_eraser_button(self):
        """
        Adds an eraser button to the color frame. When clicked, it toggles the eraser mode,
        allowing the user to erase parts of their drawing.
        """
        self.eraser_btn = ttk.Button(self.root, text='Eraser', style="Eraser.TButton", command=self.toggle_eraser)
        self.eraser_btn.pack(side='left', padx=5, in_=self.color_frame)

    def setup_active_color_button(self):
        """
        Adds a button to the color frame that toggles the active color mode.
        When active, the user can draw with the previously selected color. Otherwise, the drawing color defaults to white.
        """
        self.active_color_btn = ttk.Button(self.root, text='Active Color', style="Eraser.TButton", command=self.toggle_active_color)
        self.active_color_btn.pack(side='left', padx=5, in_=self.color_frame)

    def setup_brush_thickness_selection(self):
        """
        Adds a slider to the color frame for selecting the brush thickness.
        The thickness can be adjusted from 1 to 40, with a default value of 10.
        """
        self.brush_thickness_label = ttk.Label(self.color_frame, text="Thickness:")
        self.brush_thickness_label.pack(side='left', padx=5, in_=self.color_frame)
        self.brush_thickness = ttk.Scale(self.color_frame, from_=1, to=40, orient='horizontal', style="Horizontal.TScale")
        self.brush_thickness.set(10)  # default thickness
        self.brush_thickness.pack(side='left', padx=5, in_=self.color_frame)

    def setup_canvas(self):
        """
        Sets up the main drawing canvas, taking up the majority of the application window.
        The canvas background is set to black, and its size is dynamically adjusted based on the screen size.
        """
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.canvas = Canvas(self.root, bg='black', width=screen_width, height=screen_height - self.color_frame.winfo_reqheight())
        self.canvas.pack(padx=10, pady=5)

    def bind_canvas_events(self):
        """
        Binds mouse events to the canvas to handle drawing actions.
        '<B1-Motion>' is bound to the painting action, and '<ButtonRelease-1>' is bound to resetting the last position.
        """
        self.canvas.bind('<B1-Motion>', self.paint)
        self.canvas.bind('<ButtonRelease-1>', self.reset_last_pos)

    def initialize_other_attributes(self):
        """
        Initializes various attributes used in the application, including the default color, eraser state,
        and variables for tracking drawing speed and direction.
        """
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
        """
        Opens a color dialog to choose a new color and updates the active color.
        """
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
        """
        Toggles the eraser mode on and off.
        """
        self.eraser_active = not self.eraser_active
        if self.eraser_active:
            self.eraser_btn.configure(style="ActiveEraser.TButton")
        else:
            self.eraser_btn.configure(style="Eraser.TButton")

    def toggle_active_color(self):
        """
        Toggles the active color mode, allowing the user to switch between the active color and white.
        """
        self.active_color_flag = not self.active_color_flag
        if self.active_color_flag:
            self.active_color_btn.configure(style="ActiveEraser.TButton")
        else:
            self.active_color_btn.configure(style="Eraser.TButton")

    def paint(self, event):
        """
        Handles the painting action on the canvas when the mouse is moved with the button pressed.
        
        Parameters:
            event: The event that triggered the painting action.
        """
        paint_color = self.determine_paint_color()
        current_time = time.time()
        self.calculate_speed(current_time, event)
        self.draw_shape(event, paint_color)
        self.analyze_direction_and_speed(event)
        self.update_position_and_time(event, current_time)

    def determine_paint_color(self):
        """
        Determines the paint color based on the eraser's state.
        Returns black ('#000000') if the eraser is active, otherwise returns the currently selected color.
        """
        return '#000000' if self.eraser_active else self.color

    def calculate_speed(self, current_time, event):
        """
        Calculates the drawing speed based on the distance covered over time.
        Appends the calculated speed to the speeds list for further analysis.
        
        Parameters:
            current_time: The current time when the mouse event was triggered.
            event: The mouse event containing the current cursor position.
        """
        if hasattr(self, 'last_time') and self.last_pos is not None:
            time_diff = current_time - self.last_time
            distance = math.sqrt((event.x - self.last_pos[0])**2 + (event.y - self.last_pos[1])**2)
            if time_diff > 0:
                speed_measure = distance / time_diff
                self.speeds.append(speed_measure)

    def draw_shape(self, event, paint_color):
        """
        Draws a shape on the canvas based on the selected brush type and color.
        The shape can be an oval, square, or line, determined by the brush_type attribute.
        
        Parameters:
            event: The mouse event containing the current cursor position.
            paint_color: The color used to paint the shape.
        """
        x, y = event.x, event.y
        size = self.brush_thickness.get()
        if self.brush_type.get() == "Oval":
            self.canvas.create_oval(x-size, y-size, x+size, y+size, fill=paint_color, outline=paint_color)
        elif self.brush_type.get() == "Square":
            self.canvas.create_rectangle(x-size, y-size, x+size, y+size, fill=paint_color, outline=paint_color)
        elif self.brush_type.get() == "Line" and self.last_pos:
            self.canvas.create_line(self.last_pos[0], self.last_pos[1], x, y, fill=paint_color, width=size, capstyle=ROUND, smooth=TRUE, splinesteps=36)

    def analyze_direction_and_speed(self, event):
        """
        Analyzes the drawing direction and speed.
        Determines the general direction of drawing (up, down, or constant) and calculates the average speed.
        Updates the trend and speed_measure attributes based on the analysis.
        
        Parameters:
            event: The mouse event containing the current cursor position.
        """
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
        """
        Updates the last known position and time of the cursor.
        This information is used for calculating speed and direction in subsequent drawing actions.
        
        Parameters:
            event: The mouse event containing the current cursor position.
            current_time: The current time when the mouse event was triggered.
        """
        self.last_pos = (event.x, event.y)
        self.last_time = current_time

    def reset_last_pos(self, event):
        """
        Resets the last position of the mouse cursor to None after the mouse button is released.
        
        Parameters:
            event: The event that triggered the reset.
        """
        self.last_pos = None

    def capture(self):
        """
        Captures the current content of the canvas as an image.
        Calculates the bounding box of the canvas relative to the root window and uses it to capture the image.
        
        Returns:
            An image of the current canvas content.
        """
        x = self.root.winfo_rootx() + self.canvas.winfo_x()
        y = self.root.winfo_rooty() + self.canvas.winfo_y()
        x1 = x + self.canvas.winfo_width()
        y1 = y + self.canvas.winfo_height()
        return ImageGrab.grab(bbox=(x, y, x1, y1))

    def analyze(self, image):
        """
        Analyzes the captured image by sending its data along with current drawing parameters to an analysis function.
        Catches and prints any exceptions that occur during the analysis process.
        
        Parameters:
            image: The image to be analyzed.
        """
        try:
            analyse_send_data(np.array(image), self.trend, self.speed_measure, self.active_color_flag, self.color)
        except Exception as e:
            print(f"Error during analysis: {e}")

    def capture_and_analyze(self):
        """
        Captures the current canvas content and analyzes the captured image.
        This method combines the functionality of capturing the canvas content and analyzing the captured image.
        """
        image = self.capture()
        self.analyze(image)

    def capture_canvas_content(self):
        """
        Initiates a continuous process to capture and analyze the canvas content at intervals.
        This method creates a new thread to capture and analyze the canvas content without blocking the main UI thread.
        It then schedules itself to be called again after a specified delay, creating a loop that allows for continuous analysis.
        """
        analysis_thread = threading.Thread(target=self.capture_and_analyze)
        analysis_thread.start()
        self.root.after(self.capture_delay, self.capture_canvas_content)

def main():
    """
    The entry point of the application.
    This function initializes the main application window and starts the application's event loop.
    """
    root = Tk()
    app = DrawingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()