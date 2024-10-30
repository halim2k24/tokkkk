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


class HomeScreen:
    def __init__(self, root):
        self.bbox = None
        self.root = root
        self.root.title('Home Screen with Menu and Sections')
        self.root.geometry("1200x800")
        self.root.configure(bg="white")

        self.language = 'English'

        self.record_video_button, self.stop_recording_button = create_top_menu(
            self.root, self.go_home, self.upload_action, self.open_camera, self.start_recording, self.stop_recording,
            self.toggle_language, self.exit_application, self.open_picking_settings
        )

        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, "model/best2.pt")
        self.model = YOLO(model_path)

        self.main_frame = tk.Frame(self.root, bg="white")
        self.main_frame.pack(fill="both", expand=True)

        self.main_frame.columnconfigure(0, weight=2, minsize=800)
        self.main_frame.columnconfigure(1, weight=1, minsize=200)
        self.main_frame.rowconfigure(0, weight=1)

        self.image_view_frame = tk.Frame(self.main_frame, bg="white")
        self.image_view_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.results_frame = tk.Frame(self.main_frame, bg="lightgray")
        self.results_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

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

        self.image_picking_button = tk.Button(self.button_frame, text="Image Picking", command=self.image_picking,
                                              bg="blue", fg="white", font=("Helvetica", 12, "bold"), padx=20, pady=10)
        self.image_picking_button.pack(side="left", padx=10)

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

        self.total_ok_label = tk.Label(self.results_frame, text="Total OK: 0", font=("Helvetica", 12, "bold"),
                                       bg="lightgray", fg="green", anchor="w")
        self.total_ok_label.pack(pady=5, anchor="w", padx=10)

        self.total_ng_label = tk.Label(self.results_frame, text="Total NG: 0", font=("Helvetica", 12, "bold"),
                                       bg="lightgray", fg="red", anchor="w")
        self.total_ng_label.pack(pady=5, anchor="w", padx=10)

        self.count_label = tk.Label(self.results_frame, text="Count: 0", font=("Helvetica", 12, "bold"), bg="lightgray",
                                    fg="blue", anchor="w")
        self.count_label.pack(pady=5, anchor="w", padx=10)

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

    def open_picking_settings(self):
        messagebox.showinfo("Picking Settings", "Open Picking Settings")

    def open_settings(self):
        open_plc_settings(self.root)

    def update_date_time(self):
        now = datetime.now().strftime("Today: %Y-%m-%d %H:%M:%S")
        self.date_time_label.config(text=now)
        self.root.after(1000, self.update_date_time)

    def toggle_language(self):
        if self.language == 'English':
            self.language = 'Japanese'
        else:
            self.language = 'English'


    def go_home(self):
        self.stop_camera()
        messagebox.showinfo("Home", "You are on the Home screen!")


    def stop_camera(self):
        if hasattr(self, 'camera') and self.camera.IsGrabbing():
            self.camera.StopGrabbing()

    def open_camera(self):
        self.stop_camera()
        try:
            self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
            self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            self.converter = pylon.ImageFormatConverter()
            self.converter.OutputPixelFormat = pylon.PixelType_RGB8packed
            self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
            # self.grab_and_display()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open camera: {str(e)}")
            print(f"Error initializing camera: {str(e)}")


    # def grab_and_display(self):
    #     if self.camera.IsGrabbing():
    #         try:
    #             grab_result = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
    #             if grab_result.GrabSucceeded():
    #                 print("Frame grabbed successfully.")
    #                 image = self.converter.Convert(grab_result)  # Convert the image to RGB8
    #                 frame = image.GetArray()  # Get the RGB frame

    #                 # Resize the frame to fit the canvas while maintaining aspect ratio
    #                 canvas_width = self.camera_canvas.winfo_width()
    #                 canvas_height = self.camera_canvas.winfo_height()
    #                 frame_height, frame_width, _ = frame.shape
    #                 aspect_ratio = frame_width / frame_height

    #                 if canvas_width / canvas_height > aspect_ratio:
    #                     new_height = canvas_height
    #                     new_width = int(aspect_ratio * new_height)
    #                 else:
    #                     new_width = canvas_width
    #                     new_height = int(new_width / aspect_ratio)

    #                 frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

    #                 # Apply object detection
    #                 results = self.model.predict(source=frame, task="detect", show=False)
    #                 filtered_results = []
    #                 inside_count = 0
    #                 outside_count = 0

    #                 # Get the coordinates of the bearing and nut areas
    #                 bearing_coords = self.camera_canvas.coords(self.bearing_bbox) if self.bearing_bbox else None
    #                 nut_coords = self.camera_canvas.coords(self.nut_bbox) if self.nut_bbox else None

    #                 for result in results:
    #                     for box in result.boxes:
    #                         x1, y1, x2, y2 = box.xyxy[0]  # Ensure correct unpacking
    #                         center_x = (x1 + x2) / 2
    #                         center_y = (y1 + y2) / 2

    #                         # Check if the object is within the bearing or nut area
    #                         if (bearing_coords and bearing_coords[0] <= center_x <= bearing_coords[2] and
    #                             bearing_coords[1] <= center_y <= bearing_coords[3]) or \
    #                         (nut_coords and nut_coords[0] <= center_x <= nut_coords[2] and
    #                             nut_coords[1] <= center_y <= nut_coords[3]):
    #                             filtered_results.append((box, 'red'))  # Change color to red
    #                             inside_count += 1

    #                             # Draw a center point for objects inside the area
    #                             cv2.circle(frame, (int(center_x), int(center_y)), 5, (0, 0, 255), -1)  # Draw a red circle
    #                             cv2.putText(frame, f"({int(center_x)}, {int(center_y)})", (int(center_x), int(center_y)),
    #                                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)  # Display the x, y coordinates
    #                         else:
    #                             filtered_results.append((box, 'blue'))  # Default color is blue
    #                             outside_count += 1

    #                 # Print the counts to the console
    #                 print(f"Objects inside the area: {inside_count}")
    #                 print(f"Objects outside the area: {outside_count}")

    #                 # Plot the filtered results with respective colors
    #                 if filtered_results:
    #                     for (box, color) in filtered_results:
    #                         x1, y1, x2, y2 = box.xyxy[0]
    #                         cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255) if color == 'red' else (255, 0, 0), 2)

    #                     result_image = Image.fromarray(frame)  # Convert the image with colored boxes to a PIL Image
    #                     imgtk = ImageTk.PhotoImage(image=result_image)
    #                     self.camera_canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
    #                     self.camera_canvas.imgtk = imgtk  # Keep a reference to the image

    #                     # Ensure the rectangles and labels are on top
    #                     self.raise_bounding_boxes()
    #             else:
    #                 print("Failed to grab frame.")
    #             grab_result.Release()
    #         except Exception as e:
    #             print(f"Error during frame grabbing: {str(e)}")
    #     else:
    #         print("Camera is not grabbing.")
    #     self.root.after(10, self.grab_and_display)




    def update_camera_frame(self):
        if self.camera.IsGrabbing():
            grab_result = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            if grab_result.GrabSucceeded():
                image = self.converter.Convert(grab_result)  # Convert the image to RGB8
                frame = image.GetArray()  # Get the RGB frame

                # Resize the frame to fit the canvas
                canvas_width = self.camera_canvas.winfo_width()
                canvas_height = self.camera_canvas.winfo_height()
                frame = cv2.resize(frame, (canvas_width, canvas_height), interpolation=cv2.INTER_AREA)

                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.camera_canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                self.camera_canvas.imgtk = imgtk

                # Ensure the rectangles and labels are on top
                self.raise_bounding_boxes()

            grab_result.Release()
        self.root.after(10, self.update_camera_frame)


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
        # self.update_camera_frame()  # Start updating the camera frame
        # self.raise_bounding_boxes()  # Ensure the rectangles are on top

        # Start grabbing and displaying frames
        self.grab_and_display()

    def stop_picking(self):
        self.stop_camera()
        messagebox.showinfo("Picking", "Stopping Picking...")

    def image_picking(self):
        self.stop_camera()
        try:
            file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
            if file_path:
                image = Image.open(file_path)
                image = image.resize((self.camera_canvas.winfo_width(), self.camera_canvas.winfo_height()), Image.ANTIALIAS)
                imgtk = ImageTk.PhotoImage(image=image)
                self.camera_canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                self.camera_canvas.imgtk = imgtk

                # Ensure the rectangles and labels are on top
                self.raise_bounding_boxes()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def upload_action(self):
        self.stop_camera()
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if file_path:
            img = Image.open(file_path)
            max_width, max_height = 1400, 800
            width_ratio = max_width / img.width
            height_ratio = max_height / img.height
            new_ratio = min(width_ratio, height_ratio)
            new_width = int(img.width * new_ratio)
            new_height = int(img.height * new_ratio)
            img = img.resize((new_width, new_height), Image.LANCZOS)
            frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            results = self.model.predict(source=frame, task="detect", show=False)
            result_image = results[0].plot()
            # result_image = Image.fromarray(cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB))
            imgtk = ImageTk.PhotoImage(image=result_image)
            self.camera_canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
            self.camera_canvas.imgtk = imgtk

            # Draw circles for each detected object and show x, y values
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0]  # Ensure correct unpacking
                    center_x = (x1 + x2) / 2
                    center_y = (y1 + y2) / 2
                    radius = ((x2 - x1) + (y2 - y1)) / 4  # Approximate radius
                    # Convert tensor values to integers
                    center_x = int(center_x.item())
                    center_y = int(center_y.item())
                    radius = int(radius.item())
                    self.camera_canvas.create_oval(center_x - radius, center_y - radius, center_x + radius,
                                                   center_y + radius, outline='red')
                    self.camera_canvas.create_text(center_x, center_y, text=f"({center_x}, {center_y})", fill='red',
                                                   anchor=tk.NW)
                    # Draw the red center point
                    self.camera_canvas.create_oval(center_x - 2, center_y - 2, center_x + 2, center_y + 2, fill='red')

            # Ensure all circles are on top of the uploaded image
            for bbox in self.bboxes:
                self.camera_canvas.tag_raise(bbox)



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