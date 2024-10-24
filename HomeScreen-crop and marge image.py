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
from picking_area import load_picking_area
from top_menu import create_top_menu


class HomeScreen:
    def __init__(self, root):
        self.converter = None
        self.label = None
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

        # Add the "Capture Image" button
        self.capture_image_button = tk.Button(self.button_frame, text="Capture Image", command=self.capture_image, bg="orange",
                                              fg="white", font=("Helvetica", 12, "bold"), padx=20, pady=10)
        self.capture_image_button.pack(side="left", padx=10)

        # Add the "Capture Video" button
        self.capture_video_button = tk.Button(self.button_frame, text="Capture Video", command=self.capture_video, bg="cyan",
                                              fg="white", font=("Helvetica", 12, "bold"), padx=20, pady=10)
        self.capture_video_button.pack(side="left", padx=10)

        self.start_button = tk.Button(self.button_frame, text="Start Picking", command=self.start_picking, bg="green",
                                      fg="white", font=("Helvetica", 12, "bold"), padx=20, pady=10)
        self.start_button.pack(side="left", padx=10)

        # Add new buttons for Picking Area One and Two
        self.picking_area_one_button = tk.Button(self.button_frame, text="Picking Area One", command=self.set_picking_area_one,
                                                 bg="purple", fg="white", font=("Helvetica", 12, "bold"), padx=20, pady=10)
        self.picking_area_one_button.pack(side="left", padx=10)

        self.picking_area_two_button = tk.Button(self.button_frame, text="Picking Area Two", command=self.set_picking_area_two,
                                                 bg="brown", fg="white", font=("Helvetica", 12, "bold"), padx=20, pady=10)
        self.picking_area_two_button.pack(side="left", padx=10)

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

        self.bbox_area_one = None
        self.label_area_one = None
        self.bbox_area_two = None  # Initialize bbox_area_two
        self.label_area_two = None  # Initialize label_area_two
        # Load both picking areas on initialization
        self.load_picking_areas()

        # Initialize coordinates
        self.start_x_one = None
        self.start_y_one = None
        self.end_x_one = None
        self.end_y_one = None

        self.start_x_two = None
        self.start_y_two = None
        self.end_x_two = None
        self.end_y_two = None

    def set_picking_area_one(self):
        self.set_picking_area("picking_area_one.json", "Area One")

    def set_picking_area_two(self):
        self.set_picking_area("picking_area_two.json", "Area Two")

    def set_picking_area(self, filename, label):
        # Clear previous area if it exists
        if label == "Area One" and self.bbox_area_one:
            self.camera_canvas.delete(self.bbox_area_one)
            self.camera_canvas.delete(self.label_area_one)
            self.bbox_area_one = None
            self.label_area_one = None
        elif label == "Area Two" and self.bbox_area_two:
            self.camera_canvas.delete(self.bbox_area_two)
            self.camera_canvas.delete(self.label_area_two)
            self.bbox_area_two = None
            self.label_area_two = None

        # Bind mouse events to draw a new bounding box
        self.camera_canvas.bind("<ButtonPress-1>", lambda event: self.on_button_press(event, label))
        self.camera_canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.camera_canvas.bind("<ButtonRelease-1>", lambda event: self.on_button_release(event, filename, label))

    def on_button_press(self, event, label):
        self.start_x = event.x
        self.start_y = event.y
        self.bbox = self.camera_canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red")
        self.label = self.camera_canvas.create_text(self.start_x, self.start_y - 10, text=label, fill='red', anchor=tk.SW)

    def on_mouse_drag(self, event):
        cur_x, cur_y = (event.x, event.y)
        self.camera_canvas.coords(self.bbox, self.start_x, self.start_y, cur_x, cur_y)
        self.camera_canvas.coords(self.label, self.start_x, self.start_y - 10)

    def on_button_release(self, event, filename, label):
        self.end_x, self.end_y = (event.x, event.y)
        self.camera_canvas.unbind("<ButtonPress-1>")
        self.camera_canvas.unbind("<B1-Motion>")
        self.camera_canvas.unbind("<ButtonRelease-1>")
        messagebox.showinfo("Picking Area", f"Picking area set from ({self.start_x}, {self.start_y}) to ({self.end_x}, {self.end_y})")
        
        # Save the picking area to the specified file
        self.save_picking_area(filename, label)

        # Store the new bounding box in the correct variable
        if label == "Area One":
            self.start_x_one, self.start_y_one, self.end_x_one, self.end_y_one = self.start_x, self.start_y, self.end_x, self.end_y
            self.bbox_area_one = self.bbox
            self.label_area_one = self.label
        elif label == "Area Two":
            self.start_x_two, self.start_y_two, self.end_x_two, self.end_y_two = self.start_x, self.start_y, self.end_x, self.end_y
            self.bbox_area_two = self.bbox
            self.label_area_two = self.label

        # Raise the new bounding box to ensure it's visible
        self.raise_bounding_boxes()

        # Draw the overlay
        self.draw_overlay()

    def save_picking_area(self, filename, label):
        picking_area = {
            "start_x": self.start_x,
            "start_y": self.start_y,
            "end_x": self.end_x,
            "end_y": self.end_y
        }
        with open(filename, "w") as f:
            json.dump(picking_area, f)

    def load_picking_areas(self):
        self.load_picking_area_from_file("picking_area_one.json", "Area One")
        self.load_picking_area_from_file("picking_area_two.json", "Area Two")

    def load_picking_area_from_file(self, filename, label):
        if os.path.exists(filename):
            with open(filename, "r") as f:
                picking_area = json.load(f)
                start_x = picking_area["start_x"]
                start_y = picking_area["start_y"]
                end_x = picking_area["end_x"]
                end_y = picking_area["end_y"]
                if label == "Area One":
                    self.bbox_area_one = self.camera_canvas.create_rectangle(start_x, start_y, end_x, end_y, outline="red")
                    self.label_area_one = self.camera_canvas.create_text(start_x, start_y - 10, text=label, fill='red', anchor=tk.SW)
                elif label == "Area Two":
                    self.bbox_area_two = self.camera_canvas.create_rectangle(start_x, start_y, end_x, end_y, outline="red")
                    self.label_area_two = self.camera_canvas.create_text(start_x, start_y - 10, text=label, fill='red', anchor=tk.SW)
                self.raise_bounding_boxes()

    def raise_bounding_boxes(self):
        # Ensure all bounding boxes and labels are on top
        if self.bbox_area_one:
            self.camera_canvas.tag_raise(self.bbox_area_one)
        if self.label_area_one:
            self.camera_canvas.tag_raise(self.label_area_one)
        if self.bbox_area_two:
            self.camera_canvas.tag_raise(self.bbox_area_two)
        if self.label_area_two:
            self.camera_canvas.tag_raise(self.label_area_two)

    def picking_area_one(self):
        messagebox.showinfo("Picking Area One", "Picking Area One selected")

    def picking_area_two(self):
        messagebox.showinfo("Picking Area Two", "Picking Area Two selected")

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
        # Stop the camera if it is grabbing
        if hasattr(self, 'camera') and self.camera.IsGrabbing():
            self.camera.StopGrabbing()
            self.camera.Close()  # Ensure the camera is properly closed



    def grab_and_display(self):
        if self.camera.IsGrabbing():
            grab_result = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            if grab_result.GrabSucceeded():
                image = self.converter.Convert(grab_result)  # Convert the image to RGB8
                frame = image.GetArray()  # Get the RGB frame

                # Convert the frame to a PIL Image
                pil_image = Image.fromarray(frame)

                # Get the canvas dimensions
                canvas_width = self.camera_canvas.winfo_width()
                canvas_height = self.camera_canvas.winfo_height()

                # Calculate the scaling factor to maintain aspect ratio
                img_width, img_height = pil_image.size
                width_ratio = canvas_width / img_width
                height_ratio = canvas_height / img_height
                scale_factor = min(width_ratio, height_ratio)

                # Resize the image to fit within the canvas
                new_width = int(img_width * scale_factor)
                new_height = int(img_height * scale_factor)
                resized_image = pil_image.resize((new_width, new_height), Image.LANCZOS)

                imgtk = ImageTk.PhotoImage(image=resized_image)
                self.camera_canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                self.camera_canvas.imgtk = imgtk

                # Ensure the picking area boxes are on top of the image
                self.raise_bounding_boxes()

            grab_result.Release()
            self.camera_canvas.after(10, self.grab_and_display)



    def open_camera(self):
        self.stop_camera()
        # Initialize camera and converter
        self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        self.converter = pylon.ImageFormatConverter()
        self.converter.OutputPixelFormat = pylon.PixelType_RGB8packed
        self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

        self.grab_and_display()

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
        self.open_camera()
        self.crop_and_save_areas()  # Call the method to crop and save images

    def crop_and_save_areas(self):
        # Capture the current frame from the camera
        grab_result = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
        if grab_result.GrabSucceeded():
            image = self.converter.Convert(grab_result)  # Convert the image to RGB8
            frame = image.GetArray()  # Get the RGB frame
            # frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
            pil_image = Image.fromarray(frame)

            # Save the full frame image
            full_frame_path = "current_frame.png"
            pil_image.save(full_frame_path)
            print(f"Full frame image saved as {full_frame_path}")

            # Convert the full frame to grayscale
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            gray_pil_image = Image.fromarray(gray_frame)

            # Save the grayscale full frame image
            gray_frame_path = "current_frame_gray.png"
            gray_pil_image.save(gray_frame_path)
            print(f"Grayscale full frame image saved as {gray_frame_path}")

            # Convert the grayscale image back to RGB for merging
            rgb_base_image = gray_pil_image.convert("RGB")

            # Get actual image size
            actual_width, actual_height = pil_image.size

            # Calculate scaling factors based on the displayed image
            canvas_width = self.camera_canvas.winfo_width()
            canvas_height = self.camera_canvas.winfo_height()
            width_ratio = canvas_width / actual_width
            height_ratio = canvas_height / actual_height
            scale_factor = min(width_ratio, height_ratio)

            # Initialize a list to store cropped images and their positions
            crops_and_positions = []

            # Crop and save Area One
            if None not in (self.start_x_one, self.start_y_one, self.end_x_one, self.end_y_one):
                # Adjust coordinates based on the scaling factor
                x1 = int(self.start_x_one / scale_factor)
                y1 = int(self.start_y_one / scale_factor)
                x2 = int(self.end_x_one / scale_factor)
                y2 = int(self.end_y_one / scale_factor)

                # Print the crop coordinates for Area One
                print(f"Area One crop coordinates: x1={x1}, y1={y1}, x2={x2}, y2={y2}")

                # Ensure coordinates are within the image bounds
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(actual_width, x2)
                y2 = min(actual_height, y2)

                # Crop the first image from Area One
                area_one_crop = pil_image.crop((x1, y1, x2, y2))
                area_one_crop.save("area_one_crop.png")
                print("Area One cropped and saved as area_one_crop.png.")

                # Add to list for merging
                crops_and_positions.append((area_one_crop, (x1, y1)))

            # Crop and save Area Two
            if None not in (self.start_x_two, self.start_y_two, self.end_x_two, self.end_y_two):
                # Adjust coordinates based on the scaling factor
                x1 = int(self.start_x_two / scale_factor)
                y1 = int(self.start_y_two / scale_factor)
                x2 = int(self.end_x_two / scale_factor)
                y2 = int(self.end_y_two / scale_factor)

                # Print the crop coordinates for Area Two
                print(f"Area Two crop coordinates: x1={x1}, y1={y1}, x2={x2}, y2={y2}")

                # Ensure coordinates are within the image bounds
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(actual_width, x2)
                y2 = min(actual_height, y2)

                # Crop the first image from Area Two
                area_two_crop = pil_image.crop((x1, y1, x2, y2))
                area_two_crop.save("area_two_crop.png")
                print("Area Two cropped and saved as area_two_crop.png.")

                # Add to list for merging
                crops_and_positions.append((area_two_crop, (x1, y1)))

            # Merge the cropped images onto the RGB base image
            for crop, position in crops_and_positions:
                rgb_base_image.paste(crop, position)

            # Save the merged image
            merged_image_path = "merged_image.png"
            rgb_base_image.save(merged_image_path)
            print(f"Merged image saved as {merged_image_path}")

        grab_result.Release()

    def grab_and_display_with_detection(self):
        if self.camera.IsGrabbing():
            grab_result = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            if grab_result.GrabSucceeded():
                image = self.converter.Convert(grab_result)  # Convert the image to RGB8
                frame = image.GetArray()  # Get the RGB frame
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)

                # Perform object detection using YOLO
                results = self.model.predict(source=frame, task="detect", show=False)
                detections = results[0].boxes  # Get the detected bounding boxes

                filtered_detections = []
                for detection in detections:
                    box = detection.xyxy[0]  # Get the bounding box coordinates
                    if self.is_within_area(box, "Area One") or self.is_within_area(box, "Area Two"):
                        filtered_detections.append(detection)

                # Only plot the filtered detections
                if filtered_detections:
                    result_image_np = results[0].plot(filtered_detections)
                else:
                    result_image_np = frame  # Display original frame if no valid detections

                # Convert the result image to PIL Image format for display
                result_image = Image.fromarray(result_image_np)

                # Set the desired pixel dimensions
                desired_width = 2590 // 4
                desired_height = 1942 // 4
                
                # Resize the image to the desired dimensions
                result_image = result_image.resize((desired_width, desired_height), Image.LANCZOS)

                imgtk = ImageTk.PhotoImage(image=result_image)
                self.camera_canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                self.camera_canvas.imgtk = imgtk

                # Ensure the picking area boxes are on top of the image
                self.raise_bounding_boxes()

            grab_result.Release()
            self.camera_canvas.after(10, self.grab_and_display_with_detection)


    def stop_picking(self):
        self.stop_camera()  # Ensure the camera is stopped
        messagebox.showinfo("Picking", "Stopping Picking...")

    def upload_action(self):
        self.stop_camera()  # Stop any ongoing camera or video capture processes
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if file_path:
            img = Image.open(file_path)

            # Resize the image while maintaining aspect ratio
            canvas_width = self.camera_canvas.winfo_width()
            canvas_height = self.camera_canvas.winfo_height()
            img_width, img_height = img.size
            width_ratio = canvas_width / img_width
            height_ratio = canvas_height / img_height
            new_ratio = min(width_ratio, height_ratio)
            new_width = int(img_width * new_ratio)
            new_height = int(img_height * new_ratio)
            img = img.resize((new_width, new_height), Image.LANCZOS)

            # frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            results = self.model.predict(source=img, task="segment", show=False)
            result_image = results[0].plot()
            result_image = Image.fromarray(result_image)
            imgtk = ImageTk.PhotoImage(image=result_image)
            self.camera_canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
            self.camera_canvas.imgtk = imgtk

            # Ensure all circles and bounding boxes are on top of the uploaded image
            self.raise_bounding_boxes()

    def exit_application(self):
        self.root.quit()
        if hasattr(self, 'cap'):
            self.cap.release()
        cv2.destroyAllWindows()

    def capture_image(self):
        self.stop_camera()  # Ensure the camera is stopped
        # Placeholder for the capture image logic
        print("Image captured!")

    def capture_video(self):
        self.stop_camera()  # Ensure the camera is stopped
        # Placeholder for the capture video logic
        print("Video capture started!")

    def draw_overlay(self):
        # Clear any existing overlay
        self.camera_canvas.delete("overlay")

        # Draw a semi-transparent gray rectangle over the entire canvas
        canvas_width = self.camera_canvas.winfo_width()
        canvas_height = self.camera_canvas.winfo_height()
        self.camera_canvas.create_rectangle(0, 0, canvas_width, canvas_height, fill='gray', stipple='gray50', tags="overlay")

        # Cut out the area inside the red bounding box
        if self.bbox_area_one:
            coords = self.camera_canvas.coords(self.bbox_area_one)
            self.camera_canvas.create_rectangle(*coords, fill='', outline='', tags="overlay")

        if self.bbox_area_two:
            coords = self.camera_canvas.coords(self.bbox_area_two)
            self.camera_canvas.create_rectangle(*coords, fill='', outline='', tags="overlay")

    def adjust_brightness_contrast(self, image, brightness=0, contrast=0):
        # Adjust brightness and contrast
        beta = brightness
        alpha = contrast / 127 + 1
        adjusted = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
        return adjusted
    

    def grab_and_display_with_detection(self):
        if self.camera.IsGrabbing():
            grab_result = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            if grab_result.GrabSucceeded():
                image = self.converter.Convert(grab_result)  # Convert the image to RGB8
                frame = image.GetArray()  # Get the RGB frame
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)

                # Perform object detection using YOLO
                results = self.model.predict(source=frame, task="detect", show=False)
                detections = results[0].boxes  # Get the detected bounding boxes

                filtered_detections = []
                for detection in detections:
                    box = detection.xyxy[0]  # Get the bounding box coordinates
                    if self.is_within_area(box, "Area One") or self.is_within_area(box, "Area Two"):
                        filtered_detections.append(detection)

                # Only plot the filtered detections
                if filtered_detections:
                    result_image_np = results[0].plot(filtered_detections)
                else:
                    result_image_np = frame  # Display original frame if no valid detections

                # Convert the result image to PIL Image format for display
                result_image = Image.fromarray(result_image_np)

                # Set the desired pixel dimensions
                desired_width = 2590 // 4
                desired_height = 1942 // 4
                
                # Resize the image to the desired dimensions
                result_image = result_image.resize((desired_width, desired_height), Image.LANCZOS)

                imgtk = ImageTk.PhotoImage(image=result_image)
                self.camera_canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                self.camera_canvas.imgtk = imgtk

                # Ensure the picking area boxes are on top of the image
                self.raise_bounding_boxes()

            grab_result.Release()
            self.camera_canvas.after(10, self.grab_and_display_with_detection)

    def is_within_area(self, box, area_label):
        # box is the bounding box of the detected object [x1, y1, x2, y2]
        x1, y1, x2, y2 = box

        if area_label == "Area One":
            if None in (self.start_x_one, self.start_y_one, self.end_x_one, self.end_y_one):
                return False
            # Ensure the entire object is within the Area One bounding box
            return (self.start_x_one <= x1 <= self.end_x_one and
                    self.start_y_one <= y1 <= self.end_y_one and
                    self.start_x_one <= x2 <= self.end_x_one and
                    self.start_y_one <= y2 <= self.end_y_one)

        elif area_label == "Area Two":
            if None in (self.start_x_two, self.start_y_two, self.end_x_two, self.end_y_two):
                return False
            # Ensure the entire object is within the Area Two bounding box
            return (self.start_x_two <= x1 <= self.end_x_two and
                    self.start_y_two <= y1 <= self.end_y_two and
                    self.start_x_two <= x2 <= self.end_x_two and
                    self.start_y_two <= y2 <= self.end_y_two)

        return False





















