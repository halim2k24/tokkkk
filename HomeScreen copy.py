import os
import tkinter as tk
from tkinter import messagebox, filedialog
import cv2
import numpy as np
from PIL import Image, ImageTk
from ultralytics import YOLO
from pypylon import pylon
from datetime import datetime
import json  # Import the json module
from plcsetting import open_plc_settings
from picking_area import set_picking_area, load_picking_area
from top_menu import create_top_menu
from PickingCondations import PickingConditions
import sys


class HomeScreen:
    def __init__(self, root):
        self.bbox = None
        self.root = root
        self.root.title('Home Screen with Menu and Sections')
        self.root.geometry("1200x800")
        self.root.configure(bg="white")

        self.language = 'English'

        create_top_menu(
            self.root, 
            self.go_home,
            self.open_camera, 
            self.toggle_language, 
            self.exit_application, 
            self.open_picking_settings,
            open_plc_settings
        )

        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, "model/best2024-11-1.pt")
        self.model = YOLO(model_path)

        self.main_frame = tk.Frame(self.root, bg="white")
        self.main_frame.pack(fill="both", expand=True)

        self.main_frame.columnconfigure(0, weight=2, minsize=800)
        self.main_frame.columnconfigure(1, weight=1, minsize=200)
        self.main_frame.rowconfigure(0, weight=1)

        self.image_view_frame = tk.Frame(self.main_frame, bg="white")
        self.image_view_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.results_frame = tk.Frame(self.main_frame, bg="lightgray")
        self.results_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # Add a label for selecting bearing type
        self.select_bearing_label = tk.Label(
            self.results_frame, 
            text="Select Bearing:", 
            font=("Helvetica", 12, "bold"), 
            bg="lightgray", 
            fg="black", 
            anchor="w"
        )
        self.select_bearing_label.pack(pady=2, anchor="w", padx=5)

        # Define the list of bearing types
        self.bearing_types = [
            "All Bearing",
            "GR1087D",
            "HH2002A",
            "KG0216B0",
            "KG0226D",
            "KG0225D",
            "HH2026X",
            "HH2027X",
            "HH2025X",
            "HH4014X",
            "HH4013X"
        ]

        # Create a StringVar to hold the selected bearing type
        self.selected_bearing_type = tk.StringVar(value=self.bearing_types[0])

        # Create the dropdown menu (OptionMenu) for selecting bearing type
        self.bearing_dropdown = tk.OptionMenu(
            self.results_frame, 
            self.selected_bearing_type, 
            *self.bearing_types
        )
        self.bearing_dropdown.config(width=20, font=("Helvetica", 12))
        self.bearing_dropdown.pack(fill="x", pady=2, padx=5)

        # Add a label for selecting nut type
        self.select_nut_label = tk.Label(
            self.results_frame, 
            text="Select Nut Type:", 
            font=("Helvetica", 12, "bold"), 
            bg="lightgray", 
            fg="black", 
            anchor="w"
        )
        self.select_nut_label.pack(pady=2, anchor="w", padx=5)

        # Define the list of nut types
        self.nut_types = [
            "Nut Type 1",
            "Nut Type 2",
            "Nut Type 3",
            "Nut Type 4"
        ]

        # Create a StringVar to hold the selected nut type
        self.selected_nut_type = tk.StringVar(value=self.nut_types[0])

        # Create the dropdown menu (OptionMenu) for selecting nut type
        self.nut_dropdown = tk.OptionMenu(
            self.results_frame, 
            self.selected_nut_type, 
            *self.nut_types
        )
        self.nut_dropdown.config(width=20, font=("Helvetica", 12))
        self.nut_dropdown.pack(fill="x", pady=2, padx=5)

        # Add a Save button below the nut type dropdown
        self.save_button = tk.Button(
            self.results_frame, 
            text="Save", 
            command=self.save_selection, 
            bg="green", 
            fg="white", 
            font=("Helvetica", 12, "bold")
        )
        self.save_button.pack(fill="x", pady=2, padx=5)

        self.image_view_label = tk.Label(self.image_view_frame, text="Image View", font=("Helvetica", 16, "bold"),
                                         bg="white")
        self.image_view_label.pack(pady=20)

        self.results_label = tk.Label(self.results_frame, text="Results", font=("Helvetica", 16, "bold"),
                                      bg="lightgray")
        self.results_label.pack(pady=20)

        self.camera_canvas = tk.Canvas(self.image_view_frame, width=1400, height=800, bg="gray")
        self.camera_canvas.pack(pady=10)

        self.button_frame = tk.Frame(self.image_view_frame, bg="white")
        self.button_frame.pack(pady=10)


        self.start_button = tk.Button(self.button_frame, text="Start Picking", command=self.start_picking, bg="green",
                                      fg="white", font=("Helvetica", 12, "bold"), padx=20, pady=10)
        self.start_button.pack(side="left", padx=10)

        self.bearing_area_button = tk.Button(self.button_frame, text="Bearing Area", command=self.set_bearing_area,
                                             bg="purple", fg="white", font=("Helvetica", 12, "bold"), padx=20, pady=10)
        self.bearing_area_button.pack(side="left", padx=10)

        self.nut_area_button = tk.Button(self.button_frame, text="Nut Area", command=self.set_nut_area,
                                         bg="brown", fg="white", font=("Helvetica", 12, "bold"), padx=20, pady=10)
        self.nut_area_button.pack(side="left", padx=10)

        self.stop_button = tk.Button(self.button_frame, text="Stop", command=self.stop_picking, bg="red", fg="white",
                                     font=("Helvetica", 12, "bold"), padx=20, pady=10)
        self.stop_button.pack(side="left", padx=10)

        # Add a Restart button
        self.restart_button = tk.Button(
            self.button_frame, 
            text="Restart", 
            command=self.restart_app, 
            bg="orange", 
            fg="white", 
            font=("Helvetica", 12, "bold"), 
            padx=20, 
            pady=10
        )
        self.restart_button.pack(side="left", padx=10)

        self.bboxes = []
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None

        self.recording = False
        self.save_folder = None
        self.total_ok = 0
        self.total_ng = 0

        self.date_time_label = tk.Label(self.results_frame, text="", font=("Helvetica", 12, "bold"), bg="lightgray",
                                        fg="black", anchor="w")
        self.date_time_label.pack(pady=5, anchor="w", padx=10)

        self.total_bearing_label = tk.Label(
            self.results_frame, 
            text="Total Bearing: 0", 
            font=("Helvetica", 12, "bold"), 
            bg="lightgray", 
            fg="blue", 
            anchor="w"
        )
        self.total_bearing_label.pack(pady=5, anchor="w", padx=10)

        self.total_ok_label = tk.Label(
            self.results_frame, 
            text="Total OK: 0", 
            font=("Helvetica", 12, "bold"), 
            bg="lightgray", 
            fg="green", 
            anchor="w"
        )
        self.total_ok_label.pack(pady=5, anchor="w", padx=10)

        self.total_ng_label = tk.Label(
            self.results_frame, 
            text="Total NG: 0", 
            font=("Helvetica", 12, "bold"), 
            bg="lightgray", 
            fg="red", 
            anchor="w"
        )
        self.total_ng_label.pack(pady=5, anchor="w", padx=10)

        self.total_picking_label = tk.Label(
            self.results_frame, 
            text="Total Picking: 0", 
            font=("Helvetica", 12, "bold"), 
            bg="lightgray", 
            fg="purple", 
            anchor="w"
        )
        self.total_picking_label.pack(pady=5, anchor="w", padx=10)

        self.update_date_time()
        load_picking_area(self)

        # Initialize variables for drawing
        self.drawing_bearing_area = False
        self.drawing_nut_area = False
        self.bearing_bbox = None
        self.nut_bbox = None
        self.bearing_label = None
        self.nut_label = None
        self.start_x = None
        self.start_y = None

        # Load existing areas if available
        self.load_bearing_area()
        self.load_nut_area()

        self.bbox_area_one = None
        self.label_area_one = None
        self.bbox_area_two = None
        self.label_area_two = None
        self.bbox_bearing_area = None
        self.label_bearing_area = None
        self.bbox_nut_area = None
        self.label_nut_area = None

        # Load picking settings
        self.picking_box_size = self.load_picking_box_size()


# lode diffrent data from json file
    def load_picking_settings(self):
        try:
            with open('picking_settings.json', 'r') as f:
                settings = json.load(f)
                return settings.get('picking_angle', '0-180')  # Default to '0-180' if not found
        except Exception as e:
            print(f"Error loading picking settings: {e}")
            return '0-180'  # Default value if loading fails
    
    def load_bearing_area_from_json(self):
        if os.path.exists('bearing_area.json'):
            with open('bearing_area.json', 'r') as f:
                return json.load(f)
        else:
            return {'start_x': 0, 'start_y': 0, 'end_x': 800, 'end_y': 600}  # Default values
        
    
    def load_bearing_area(self):
        if os.path.exists('bearing_area.json'):
            with open('bearing_area.json', 'r') as f:
                bearing_area = json.load(f)
                self.bearing_bbox = self.camera_canvas.create_rectangle(
                    bearing_area['start_x'], bearing_area['start_y'],
                    bearing_area['end_x'], bearing_area['end_y'],
                    outline='red', tags="bearing"
                )
                self.bearing_label = self.camera_canvas.create_text(
                    bearing_area['start_x'], bearing_area['start_y'] - 10,
                    text="Bearing Area", fill="red", tags="bearing_label"
                )
                self.camera_canvas.tag_raise("bearing")
                self.camera_canvas.tag_raise("bearing_label")


    def load_nut_area(self):
        if os.path.exists('nut_area.json'):
            with open('nut_area.json', 'r') as f:
                nut_area = json.load(f)
                self.nut_bbox = self.camera_canvas.create_rectangle(
                    nut_area['start_x'], nut_area['start_y'],
                    nut_area['end_x'], nut_area['end_y'],
                    outline='red', tags="nut"
                )
                self.nut_label = self.camera_canvas.create_text(
                    nut_area['start_x'], nut_area['start_y'] - 10,
                    text="Nut Area", fill="red", tags="nut_label"
                )
                self.camera_canvas.tag_raise("nut")
                self.camera_canvas.tag_raise("nut_label")
                self.raise_bounding_boxes()

    
    def load_picking_box_size(self):
        try:
            with open('picking_settings.json', 'r') as f:
                settings = json.load(f)
                return settings.get('box_size', 60)  # Default to 60 if not found
        except Exception as e:
            print(f"Error loading picking settings: {e}")
            return 60  # Default value if loading fails


    def load_matching_value(self):
        try:
            with open('picking_settings.json', 'r') as f:
                settings = json.load(f)
                return float(settings.get('matching', 0))  # Default to 0 if not found
        except Exception as e:
            print(f"Error loading matching value: {e}")
            return 0  # Default value if loading fails
# lode diffrent data from json file

    

# open picking settings class
    def open_picking_settings(self):
        PickingConditions(self.root)

# open plc settings class   
    def open_settings(self):
        open_plc_settings(self.root)

# update date and time
    def update_date_time(self):
        now = datetime.now().strftime("Today: %Y-%m-%d %H:%M:%S")
        self.date_time_label.config(text=now)
        self.root.after(1000, self.update_date_time)

# toggle language
    def toggle_language(self):
        if self.language == 'English':
            self.language = 'Japanese'
        else:
            self.language = 'English'

# go home
    def go_home(self):
        self.stop_camera()
        # Ensure picking is stopped
        self.stop_picking()

# stop camera
    def stop_camera(self):
        if hasattr(self, 'camera') and self.camera.IsGrabbing():
            self.camera.StopGrabbing()
# open camera
    def open_camera(self):
        self.stop_camera()
        try:
            self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
            self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            self.converter = pylon.ImageFormatConverter()
            self.converter.OutputPixelFormat = pylon.PixelType_RGB8packed
            self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

            # Grab a single frame
            if self.camera.IsGrabbing():
                grab_result = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                if grab_result.GrabSucceeded():
                    image = self.converter.Convert(grab_result)  # Convert the image to RGB8
                    frame = image.GetArray()  # Get the RGB frame

                    # Resize the frame to fit the canvas while maintaining aspect ratio
                    canvas_width = self.camera_canvas.winfo_width()
                    canvas_height = self.camera_canvas.winfo_height()
                    frame_height, frame_width, _ = frame.shape
                    aspect_ratio = frame_width / frame_height

                    if canvas_width / canvas_height > aspect_ratio:
                        new_height = canvas_height
                        new_width = int(aspect_ratio * new_height)
                    else:
                        new_width = canvas_width
                        new_height = int(new_width / aspect_ratio)

                    frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

                    # Convert the frame to a format suitable for Tkinter
                    result_image = Image.fromarray(frame)
                    imgtk = ImageTk.PhotoImage(image=result_image)
                    self.camera_canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                    self.camera_canvas.imgtk = imgtk  # Keep a reference to the image

                grab_result.Release()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open camera: {str(e)}")
            print(f"Error initializing camera: {str(e)}")



    def start_recording(self):
        self.recording = True
        current_date = datetime.now().strftime("%Y%m%d")
        self.save_folder = os.path.join(os.getcwd(), current_date)
        os.makedirs(self.save_folder, exist_ok=True)
        self.record_video_button.config(state=tk.DISABLED)
        self.stop_recording_button.config(state=tk.NORMAL)

    def stop_recording(self):
        self.recording = False
        self.save_folder = None
        self.record_video_button.config(state=tk.NORMAL)
        self.stop_recording_button.config(state=tk.DISABLED)
        messagebox.showinfo("Recording", "Recording stopped and images saved.")

    def record_video(self):
        self.stop_camera()
        self.open_camera()

    def start_picking(self):
        self.stop_camera()
        # Initialize camera or video capture
        self.open_camera()  # Ensure this method correctly starts the camera
        # Start grabbing and displaying frames
        self.grab_and_display()

    def stop_picking(self):
        self.stop_camera()
        messagebox.showinfo("Picking", "Stopping Picking...")



    def exit_application(self):
        self.root.quit()
        if hasattr(self, 'cap'):
            self.cap.release()
        cv2.destroyAllWindows()



    def set_bearing_area(self):
        # Enable drawing mode for the bearing area
        self.drawing_bearing_area = True
        self.camera_canvas.bind("<ButtonPress-1>", self.on_bearing_button_press)
        self.camera_canvas.bind("<B1-Motion>", self.on_bearing_mouse_drag)
        self.camera_canvas.bind("<ButtonRelease-1>", self.on_bearing_button_release)

    def on_bearing_button_press(self, event):
        if self.drawing_bearing_area:
            self.start_x = event.x
            self.start_y = event.y
            if self.bearing_bbox:
                self.camera_canvas.delete(self.bearing_bbox)
            if self.bearing_label:
                self.camera_canvas.delete(self.bearing_label)
            self.bearing_bbox = self.camera_canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', tags="bearing")
            self.bearing_label = self.camera_canvas.create_text(self.start_x, self.start_y - 10, text="Bearing Area", fill="red", tags="bearing_label")
            self.camera_canvas.tag_raise("bearing")
            self.camera_canvas.tag_raise("bearing_label")

    def on_bearing_mouse_drag(self, event):
        if self.drawing_bearing_area and self.bearing_bbox:
            self.camera_canvas.coords(self.bearing_bbox, self.start_x, self.start_y, event.x, event.y)
            self.camera_canvas.coords(self.bearing_label, self.start_x, self.start_y - 10)
            self.camera_canvas.tag_raise("bearing")
            self.camera_canvas.tag_raise("bearing_label")

    def on_bearing_button_release(self, event):
        if self.drawing_bearing_area:
            self.drawing_bearing_area = False
            self.camera_canvas.unbind("<ButtonPress-1>")
            self.camera_canvas.unbind("<B1-Motion>")
            self.camera_canvas.unbind("<ButtonRelease-1>")
            # Save the coordinates to a JSON file
            self.save_bearing_area()

    def save_bearing_area(self):
        if self.bearing_bbox:
            coords = self.camera_canvas.coords(self.bearing_bbox)
            bearing_area = {
                'start_x': coords[0],
                'start_y': coords[1],
                'end_x': coords[2],
                'end_y': coords[3]
            }
            with open('bearing_area.json', 'w') as f:
                json.dump(bearing_area, f, indent=4)

    def set_nut_area(self):
        # Enable drawing mode for the nut area
        self.drawing_nut_area = True
        self.camera_canvas.bind("<ButtonPress-1>", self.on_nut_button_press)
        self.camera_canvas.bind("<B1-Motion>", self.on_nut_mouse_drag)
        self.camera_canvas.bind("<ButtonRelease-1>", self.on_nut_button_release)

    def on_nut_button_press(self, event):
        if self.drawing_nut_area:
            self.start_x = event.x
            self.start_y = event.y
            if self.nut_bbox:
                self.camera_canvas.delete(self.nut_bbox)
            if self.nut_label:
                self.camera_canvas.delete(self.nut_label)
            self.nut_bbox = self.camera_canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', tags="nut")
            self.nut_label = self.camera_canvas.create_text(self.start_x, self.start_y - 10, text="Nut Area", fill="red", tags="nut_label")
            self.camera_canvas.tag_raise("nut")
            self.camera_canvas.tag_raise("nut_label")

    def on_nut_mouse_drag(self, event):
        if self.drawing_nut_area and self.nut_bbox:
            self.camera_canvas.coords(self.nut_bbox, self.start_x, self.start_y, event.x, event.y)
            self.camera_canvas.coords(self.nut_label, self.start_x, self.start_y - 10)
            self.camera_canvas.tag_raise("nut")
            self.camera_canvas.tag_raise("nut_label")

    def on_nut_button_release(self, event):
        if self.drawing_nut_area:
            self.drawing_nut_area = False
            self.camera_canvas.unbind("<ButtonPress-1>")
            self.camera_canvas.unbind("<B1-Motion>")
            self.camera_canvas.unbind("<ButtonRelease-1>")
            # Save the coordinates to a JSON file
            self.save_nut_area()

    def save_nut_area(self):
        if self.nut_bbox:
            coords = self.camera_canvas.coords(self.nut_bbox)
            nut_area = {
                'start_x': coords[0],
                'start_y': coords[1],
                'end_x': coords[2],
                'end_y': coords[3]
            }
            with open('nut_area.json', 'w') as f:
                json.dump(nut_area, f, indent=4)

    def raise_bounding_boxes(self):
        # Ensure all bounding boxes and labels are on top
        if self.bearing_bbox:
            self.camera_canvas.tag_raise(self.bearing_bbox)
        if self.bearing_label:
            self.camera_canvas.tag_raise(self.bearing_label)
        if self.nut_bbox:
            self.camera_canvas.tag_raise(self.nut_bbox)
        if self.nut_label:
            self.camera_canvas.tag_raise(self.nut_label)



# picking box
    def draw_rotated_box(self, frame, center, size, angle):
        """Draw a rotated rectangle on the frame and show its center point."""
        rect = ((center[0], center[1]), (size, size), angle)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        cv2.drawContours(frame, [box], 0, (0, 255, 255), 1)  # Yellow color

        # Draw the center point
        cv2.circle(frame, (int(center[0]), int(center[1])), 3, (0, 0, 255), -1)  # Red color for center point

        # Display the center point coordinates for picking box
        cv2.putText(frame, f"({int(center[0])}, {int(center[1])})", (int(center[0]) + 5, int(center[1]) - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    def calculate_positions(self, center_x, center_y, picking_box_size, angle, distance):
        rad = np.radians(angle)
        offset_x = int(distance * np.cos(rad))
        offset_y = int(distance * np.sin(rad))

        start_x = int(center_x + offset_x - picking_box_size / 2) 
        start_y = int(center_y + offset_y - picking_box_size / 2)
        return start_x, start_y

    def draw_picking_box(self, frame, center_x, center_y, object_width, picking_box_size, ok_objects, inside_bearing_objects):
        # Load the bearing area coordinates from the JSON file
        bearing_area = self.load_bearing_area_from_json()

        # Define the bearing area boundaries
        area_x_min = bearing_area['start_x']
        area_y_min = bearing_area['start_y']
        area_x_max = bearing_area['end_x']
        area_y_max = bearing_area['end_y']

        def is_within_bearing_area(x, y, size):
            # Check if the box stays within the bearing area
            return area_x_min <= x <= area_x_max - size and area_y_min <= y <= area_y_max - size

        def is_overlapping(box, circle_center, circle_radius):
            """Check if a box overlaps with a circle."""
            box_x_min, box_y_min, box_x_max, box_y_max = box
            circle_x, circle_y = circle_center

            # Check if the circle's center is within the box
            if box_x_min <= circle_x <= box_x_max and box_y_min <= circle_y <= box_y_max:
                return True

            # Check if the distance from the circle's center to any of the box's corners is less than the circle's radius
            corners = [(box_x_min, box_y_min), (box_x_max, box_y_min), (box_x_min, box_y_max), (box_x_max, box_y_max)]
            for corner_x, corner_y in corners:
                if ((corner_x - circle_x) ** 2 + (corner_y - circle_y) ** 2) ** 0.5 < circle_radius:
                    return True

            return False

        picking_count = 0  # Initialize picking count

        # Iterate over each "ok" object and draw the picking boxes
        for obj in ok_objects:
            x1, y1, x2, y2, confidence = obj
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            object_width = x2 - x1

            # Draw a circle for the "ok" object
            radius = max(object_width, y2 - y1) / 2
            cv2.circle(frame, (int(center_x), int(center_y)), int(radius), (0, 255, 0), 2)  # Green color for "ok" objects


            # Set a scaled distance for both picking boxes
            some_threshold = 50   # Adjust this factor to control the closeness
            if object_width > some_threshold:  # Replace 'some_threshold' with the appropriate value
                scaling_factor = 0.8
            else:
                scaling_factor = 0.99
            max_distance = 100  # Set a maximum limit for the distance

            # Calculate the distance with scaling and limit it to the maximum distance
            distance = min(object_width * scaling_factor, max_distance)

            # Set a fixed distance for both picking boxes
            # distance = object_width

            # Try different angles to find non-overlapping positions for both boxes
            for angle in range(0, 360, 10):
                start_x_0, start_y_0 = self.calculate_positions(center_x, center_y, picking_box_size, angle, distance)
                start_x_180, start_y_180 = self.calculate_positions(center_x, center_y, picking_box_size, angle + 180, distance)

                box_0 = (start_x_0, start_y_0, start_x_0 + picking_box_size, start_y_0 + picking_box_size)
                box_180 = (start_x_180, start_y_180, start_x_180 + picking_box_size, start_y_180 + picking_box_size)

                # Check for overlap with any inside_bearing_objects, excluding the current object
                overlap_found = False
                for inside_obj in inside_bearing_objects:
                    ix1, iy1, ix2, iy2, _, _ = inside_obj
                    if (ix1, iy1, ix2, iy2) == (x1, y1, x2, y2):
                        continue  # Skip the current object itself

                    circle_center = ((ix1 + ix2) / 2, (iy1 + iy2) / 2)
                    circle_radius = max(ix2 - ix1, iy2 - iy1) / 2

                    if is_overlapping(box_0, circle_center, circle_radius) or is_overlapping(box_180, circle_center, circle_radius):
                        overlap_found = True
                        break

                if not overlap_found and is_within_bearing_area(start_x_0, start_y_0, picking_box_size) and is_within_bearing_area(start_x_180, start_y_180, picking_box_size):
                    self.draw_rotated_box(frame, (start_x_0 + picking_box_size // 2, start_y_0 + picking_box_size // 2), picking_box_size, angle)
                    self.draw_rotated_box(frame, (start_x_180 + picking_box_size // 2, start_y_180 + picking_box_size // 2), picking_box_size, angle + 180)
                    picking_count += 1  # Increment picking count
                    break
            else:
                # Try alternative angles if no position is found
                for angle in range(90, 450, 10):
                    start_x_90, start_y_90 = self.calculate_positions(center_x, center_y, picking_box_size, angle, distance)
                    start_x_270, start_y_270 = self.calculate_positions(center_x, center_y, picking_box_size, angle + 180, distance)

                    box_90 = (start_x_90, start_y_90, start_x_90 + picking_box_size, start_y_90 + picking_box_size)
                    box_270 = (start_x_270, start_y_270, start_x_270 + picking_box_size, start_y_270 + picking_box_size)

                    overlap_found = False
                    for inside_obj in inside_bearing_objects:
                        ix1, iy1, ix2, iy2, _, _ = inside_obj
                        if (ix1, iy1, ix2, iy2) == (x1, y1, x2, y2):
                            continue

                        circle_center = ((ix1 + ix2) / 2, (iy1 + iy2) / 2)
                        circle_radius = max(ix2 - ix1, iy2 - iy1) / 2

                        if is_overlapping(box_90, circle_center, circle_radius) or is_overlapping(box_270, circle_center, circle_radius):
                            overlap_found = True
                            break

                    if not overlap_found and is_within_bearing_area(start_x_90, start_y_90, picking_box_size) and is_within_bearing_area(start_x_270, start_y_270, picking_box_size):
                        self.draw_rotated_box(frame, (start_x_90 + picking_box_size // 2, start_y_90 + picking_box_size // 2), picking_box_size, angle)
                        self.draw_rotated_box(frame, (start_x_270 + picking_box_size // 2, start_y_270 + picking_box_size // 2), picking_box_size, angle + 180)
                        picking_count += 1  # Increment picking count
                        break
                else:
                    print("Unable to find non-overlapping positions for the picking boxes.")

        return picking_count  # Return the count of picking boxes drawn

    def grab_and_display(self):
        if self.camera.IsGrabbing():
            try:
                grab_result = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                if grab_result.GrabSucceeded():
                    print("Frame grabbed successfully.")
                    image = self.converter.Convert(grab_result)  # Convert the image to RGB8
                    frame = image.GetArray()  # Get the RGB frame

                    # Resize the frame to fit the canvas while maintaining aspect ratio
                    canvas_width = self.camera_canvas.winfo_width()
                    canvas_height = self.camera_canvas.winfo_height()
                    frame_height, frame_width, _ = frame.shape
                    aspect_ratio = frame_width / frame_height

                    if canvas_width / canvas_height > aspect_ratio:
                        new_height = canvas_height
                        new_width = int(aspect_ratio * new_height)
                    else:
                        new_width = canvas_width
                        new_height = int(new_width / aspect_ratio)

                    frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

                    # Apply object detection
                    results = self.model.predict(source=frame, task="detect", show=False)
                    bearing_coords = self.camera_canvas.coords(self.bearing_bbox) if self.bearing_bbox else None
                    nut_coords = self.camera_canvas.coords(self.nut_bbox) if self.nut_bbox else None

                    detected_objects = []  # Initialize detected_objects list
                    ok_objects = []  # List to store "ok" objects
                    inside_bearing_objects = []  # List to store all objects inside the bearing area

                    for result in results:
                        for box in result.boxes:
                            # Ensure the coordinates are correctly accessed and unpacked
                            coordinates = box.xyxy[0].cpu().numpy()  # Convert to numpy array
                            if len(coordinates) == 4:
                                x1, y1, x2, y2 = map(int, coordinates)  # Safely unpack the values
                                center_x = (x1 + x2) / 2
                                center_y = (y1 + y2) / 2
                                object_width = x2 - x1  # Width of the object

                                confidence = box.conf.item()  # Confidence score
                                label = result.names[box.cls.item()]  # Class label (assume OK or NG)

                                # Print the label and confidence level
                                print(f"Label: {label}, Confidence: {confidence:.2f}")

                                # Add the detected object to the list
                                detected_objects.append((x1, y1, x2, y2, confidence, label))

                                # Check if the object is within the bearing area
                                inside_bearing = (bearing_coords and bearing_coords[0] <= center_x <= bearing_coords[2] and
                                                bearing_coords[1] <= center_y <= bearing_coords[3])
                                matching_value = self.load_matching_value()

                                if inside_bearing:
                                    # Add to the list of objects inside the bearing area
                                    inside_bearing_objects.append((x1, y1, x2, y2, confidence, label))
                                    if confidence < matching_value / 100:
                                        label = "NG"

                                    if label == "OK":
                                        # OK object: Draw green bounding box and center point
                                        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 255, 0), 1)
                                        cv2.putText(frame, f"OK: {confidence:.2f}",
                                                    (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                                        # Draw center point for OK objects
                                        cv2.circle(frame, (int(center_x), int(center_y)), 5, (255, 255, 0), -1)
                                        cv2.putText(frame, f"({int(center_x)}, {int(center_y)})", (int(center_x), int(center_y)),
                                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

                                        # Add to the list of ok objects
                                        ok_objects.append((x1, y1, x2, y2, confidence))

                                    elif label == "NG":
                                        # NG object: Draw red bounding box, center point, and circle
                                        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 1)
                                        cv2.putText(frame, f"NG: {confidence:.2f}",
                                                    (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                                        # Draw circle for NG objects
                                        radius = max(object_width, y2 - y1) / 2
                                        self.draw_circle(frame, center_x, center_y, radius)
                                else:
                                    # Outside the bearing area: Draw gray bounding box, no labels or confidence
                                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (128, 128, 128), 1)
                            else:
                                print(f"Unexpected number of values in coordinates: {coordinates}")

                    # Draw the picking box only for OK objects
                    picking_count = 1  # Initialize picking count
                    for obj in ok_objects:
                        x1, y1, x2, y2, confidence = obj
                        center_x = (x1 + x2) / 2
                        center_y = (y1 + y2) / 2
                        object_width = x2 - x1

                        picking_count += self.draw_picking_box(frame, center_x, center_y, object_width, self.picking_box_size, ok_objects, inside_bearing_objects)

                    # Convert the result image to a format suitable for Tkinter
                    result_image = Image.fromarray(frame)
                    imgtk = ImageTk.PhotoImage(image=result_image)
                    self.camera_canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                    self.camera_canvas.imgtk = imgtk  # Keep a reference to the image

                    # Ensure the rectangles and labels are on top
                    self.raise_bounding_boxes()
                    print(inside_bearing_objects)
                    print("--------------------------------")  

                    # Example call to process_data with detected objects
                    self.process_data(detected_objects, picking_count)

                else:
                    print("Failed to grab frame.")
                grab_result.Release()
            except Exception as e:
                print(f"Error during frame grabbing: {str(e)}")
        else:
            print("Camera is not grabbing.")
        self.root.after(10, self.grab_and_display)

    def draw_circle(self, frame, center_x, center_y, radius):
        """Draw a circle from the center point that covers the full object radius."""
        cv2.circle(frame, (int(center_x), int(center_y)), int(radius), (0, 0, 255), 2)  # Red color

    def restart_app(self):
        """Restart the application."""
        self.root.destroy()  # Close the current application window
        os.execl(sys.executable, sys.executable, *sys.argv)  # Restart the application

    def update_results(self, ok_count, ng_count, picking_count):
        """Update the results labels with current frame values."""
        total_bearing = ok_count + ng_count

        # Update the labels
        self.total_bearing_label.config(text=f"Total Bearing: {total_bearing}")
        self.total_ok_label.config(text=f"Total OK: {ok_count}")
        self.total_ng_label.config(text=f"Total NG: {ng_count}")

        # Update the total picking label with half the picking count
        self.total_picking_label.config(text=f"Total Picking: {picking_count // 2}")

        # Debugging: Print the current frame values
        print(f"Current Frame - Total Bearing: {total_bearing}, OK: {ok_count}, NG: {ng_count}, Picking: {picking_count // 2}")

    def process_data(self, detected_objects, picking_count):
        """Process detected objects and update results for the current frame."""
        ok_count = 0
        ng_count = 0

        for obj in detected_objects:
            label = obj[-1]  # Assuming the label is the last item in the tuple
            if label == "OK":
                ok_count += 1
            elif label == "NG":
                ng_count += 1

        # Update the results with the counts from this frame
        self.update_results(ok_count, ng_count, picking_count)

        # Debugging: Print detected objects
        print(f"Detected Objects: {detected_objects}")

    def save_selection(self):
        # Implement the logic to save the selected bearing and nut types
        selected_bearing = self.selected_bearing_type.get()
        selected_nut = self.selected_nut_type.get()
        print(f"Selected Bearing: {selected_bearing}, Selected Nut: {selected_nut}")
        # Add any additional save logic here

    