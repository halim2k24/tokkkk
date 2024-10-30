import tkinter as tk
from tkinter import ttk
import json
import os
import sys

class PickingConditions:
    def __init__(self, parent):
        # Create new window
        self.window = tk.Toplevel(parent)
        self.window.title("Picking Conditions")
        self.window.geometry("300x400")

        # Center the window on the screen
        self.center_window()

        # Load existing settings
        self.load_existing_settings()

        # Create labels and entry fields for inputs
        tk.Label(self.window, text="Matching %").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.matching_entry = tk.Entry(self.window)
        self.matching_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(self.window, text="Detection Order").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.detection_order = ttk.Combobox(self.window, values=["Ascending X", "Ascending Y", "Descending X", "Descending Y", "Matching %"])
        self.detection_order.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(self.window, text="Detection Count").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.detection_count = tk.Entry(self.window)
        self.detection_count.grid(row=2, column=1, padx=10, pady=5)

        tk.Label(self.window, text="Angle Range").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.picking_angle = ttk.Combobox(self.window, values=["0-180", "90-270"])
        self.picking_angle.grid(row=3, column=1, padx=10, pady=5)

        # Box size with slider
        tk.Label(self.window, text="Box Size").grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.box_size_slider = tk.Scale(self.window, from_=10, to=100, orient=tk.HORIZONTAL)
        self.box_size_slider.grid(row=5, column=1, padx=10, pady=5)

        # Set the entry fields with existing values if they exist
        self.set_existing_values()

        # Update Button
        self.update_button = tk.Button(self.window, text="Update", command=self.update_settings)
        self.update_button.grid(row=6, columnspan=2, pady=20)

    def load_existing_settings(self):
        # Path to load the existing JSON settings
        self.json_file_path = os.path.join(os.getcwd(), 'picking_settings.json')
        if os.path.exists(self.json_file_path):
            with open(self.json_file_path, 'r') as json_file:
                self.existing_settings = json.load(json_file)
        else:
            # If the file doesn't exist, create a default dictionary
            self.existing_settings = {
                "matching": "",
                "detection_order": "",
                "detection_count": "",
                "picking_angle": "",
                "box_size": 49
            }

    def set_existing_values(self):
        """Set the initial values in the input fields based on the existing settings."""
        if self.existing_settings["matching"]:
            self.matching_entry.insert(0, self.existing_settings["matching"])
        if self.existing_settings["detection_order"]:
            self.detection_order.set(self.existing_settings["detection_order"])
        if self.existing_settings["detection_count"]:
            self.detection_count.insert(0, self.existing_settings["detection_count"])
        if self.existing_settings["picking_angle"]:
            self.picking_angle.set(self.existing_settings["picking_angle"])
        self.box_size_slider.set(self.existing_settings["box_size"])

    def update_settings(self):
        # Logic to handle the input values. Keep old values if fields are left empty.
        matching = self.matching_entry.get() if self.matching_entry.get() else self.existing_settings["matching"]
        detection_order = self.detection_order.get() if self.detection_order.get() else self.existing_settings["detection_order"]
        detection_count = self.detection_count.get() if self.detection_count.get() else self.existing_settings["detection_count"]
        picking_angle = self.picking_angle.get() if self.picking_angle.get() else self.existing_settings["picking_angle"]
        box_size = self.box_size_slider.get()  # Slider always returns a value

        # Updated settings
        updated_settings = {
            "matching": matching,
            "detection_order": detection_order,
            "detection_count": detection_count,
            "picking_angle": picking_angle,
            "box_size": box_size
        }

        # Write the updated settings to the JSON file
        with open(self.json_file_path, 'w') as json_file:
            json.dump(updated_settings, json_file, indent=4)

        print("Settings updated and saved to picking_settings.json")

        # Restart the application after saving settings
        self.restart_application()

    def center_window(self):
        # Get the screen width and height
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()

        # Calculate the center point
        window_width = 300  # Width of the window
        window_height = 400  # Height of the window
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)

        # Set the window position
        self.window.geometry(f'{window_width}x{window_height}+{x}+{y}')

    def restart_application(self):
        """Close the current application and restart it."""
        self.window.destroy()  # Close the settings window
        self.window.quit()  # Close the parent Tkinter window
        
        # Restart the app by calling python executable again with the current script
        python = sys.executable
        os.execl(python, python, *sys.argv)
