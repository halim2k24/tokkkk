import tkinter as tk
from about import show_about
from plcsetting import open_plc_settings

def create_top_menu(root, home_callback, open_camera_callback, toggle_language_callback, exit_callback, picking_settings_callback, open_plc_settings_callback):
    top_frame = tk.Frame(root, bg="white")
    top_frame.pack(side="top", fill="x")

    home_button = tk.Button(top_frame, text="Home", command=home_callback, bg="black", fg="white",
                            font=("Helvetica", 12, "bold"), padx=20, pady=10)
    home_button.pack(side="left", padx=10)

    open_camera_button = tk.Button(top_frame, text="Open Camera", command=open_camera_callback, bg="blue",
                                   fg="white", font=("Helvetica", 12, "bold"), padx=20, pady=10)
    open_camera_button.pack(side="left", padx=10)

    picking_settings_button = tk.Button(top_frame, text="Picking Settings", command=picking_settings_callback, bg="gray",
                                        fg="white", font=("Helvetica", 12, "bold"), padx=20, pady=10)
    picking_settings_button.pack(side="left", padx=10)

    change_language_button = tk.Button(top_frame, text="Change Language", command=toggle_language_callback,
                                       bg="gray", fg="white", font=("Helvetica", 12, "bold"), padx=20, pady=10)
    change_language_button.pack(side="left", padx=10)

    plc_settings_button = tk.Button(top_frame, text="PLC Settings", command=open_plc_settings_callback, bg="gray",
                                    fg="white", font=("Helvetica", 12, "bold"), padx=20, pady=10)
    plc_settings_button.pack(side="left", padx=10)

    exit_button = tk.Button(top_frame, text="Exit", command=exit_callback, bg="black", fg="white",
                            font=("Helvetica", 12, "bold"), padx=20, pady=10)
    exit_button.pack(side="left", padx=10)
