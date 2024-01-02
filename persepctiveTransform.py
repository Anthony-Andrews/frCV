import cv2
import numpy as np
import os
import tkinter as tk
from tkinter import Entry, Label, Button, filedialog, Scale
import json

class VideoProcessor:
    def __init__(self):
        self.video_path = None
        self.cap = None
        self.paused = False
        self.width, self.height = 1920, 1080
        self.speed = 1.0
        self.output_width, self.output_height = self.width, self.height
        self.src_points = np.array([[528, 302], [1477, 302], [1889, 523], [117, 496]], dtype=np.float32)
        self.dst_points = np.array([[0, 0], [self.width - 1, 0], [self.width - 1, self.height - 1], [0, self.height - 1]],
                                   dtype=np.float32)
        self.overlay_image_path = os.path.join(os.path.dirname(__file__), "field.png")
        self.overlay_image = cv2.imread(self.overlay_image_path)

        if self.overlay_image is None:
            print(f"Error: Unable to load overlay image from {self.overlay_image_path}")
            exit()

        self.opacity = 0.5
        self.rotation_angle = 0.0

        self.M = cv2.getPerspectiveTransform(self.src_points, self.dst_points)

        # Create the main Tkinter window
        self.root = tk.Tk()
        self.root.title("Perspective Transform Video Tool")

        # Create entry fields for adjusting pixel coordinates
        self.entry_fields = []

        for i, label_text in enumerate(["Top-Left", "Top-Right", "Bottom-Right", "Bottom-Left"]):
            x_label = Label(self.root, text=f"{label_text} - X:")
            x_label.grid(row=i, column=0, padx=5, pady=5)

            x_entry = Entry(self.root)
            x_entry.insert(0, str(self.src_points[i, 0]))
            x_entry.grid(row=i, column=1, padx=5, pady=5)

            y_label = Label(self.root, text=f"{label_text} - Y:")
            y_label.grid(row=i, column=2, padx=5, pady=5)

            y_entry = Entry(self.root)
            y_entry.insert(0, str(self.src_points[i, 1]))
            y_entry.grid(row=i, column=3, padx=5, pady=5)

            self.entry_fields.extend([x_entry, y_entry])

        # Create buttons for actions
        self.create_action_buttons()

        # Create entry fields for adjusting output resolution
        self.create_resolution_fields()

        # Create entry field for adjusting speed
        speed_label = Label(self.root, text="Speed:")
        speed_label.grid(row=9, column=2, pady=5)

        self.speed_entry = Entry(self.root)
        self.speed_entry.insert(0, str(self.speed))
        self.speed_entry.grid(row=9, column=3, pady=5)

        # Create slider for adjusting opacity
        opacity_label = Label(self.root, text="Opacity:")
        opacity_label.grid(row=10, column=2, pady=5)

        self.opacity_scale = Scale(self.root, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL, length=200)
        self.opacity_scale.set(self.opacity)
        self.opacity_scale.grid(row=10, column=3, pady=5)

        # Entry field for adjusting rotation
        rotation_label = Label(self.root, text="Rotation (degrees):")
        rotation_label.grid(row=9, column=0, pady=5)

        self.rotation_entry = Entry(self.root)
        self.rotation_entry.insert(0, str(self.rotation_angle))
        self.rotation_entry.grid(row=9, column=1, pady=5)

        # Create buttons for adjusting X and Y coordinates
        offset_label = Label(self.root, text="Offsets:")
        offset_label.grid(row=11, column=0, pady=1)

        x_up_button = Button(self.root, text="Left", command=lambda: self.adjust_offset(-1, 0))
        x_up_button.grid(row=13, column=0, pady=5)

        x_down_button = Button(self.root, text="Right", command=lambda: self.adjust_offset(1, 0))
        x_down_button.grid(row=13, column=2, pady=5)

        y_left_button = Button(self.root, text="Up", command=lambda: self.adjust_offset(0, -1))
        y_left_button.grid(row=12, column=1, pady=5)

        y_right_button = Button(self.root, text="Down", command=lambda: self.adjust_offset(0, 1))
        y_right_button.grid(row=14, column=1, pady=5)

        # Start the Tkinter main loop
        self.root.after(0, self.process_video)
        self.root.mainloop()

    def create_action_buttons(self):
        # Create buttons for actions
        self.pause_button = Button(self.root, text="Pause", command=self.toggle_pause)
        self.pause_button.grid(row=7, column=0, pady=5)

        rewind_button = Button(self.root, text="Rewind", command=self.rewind_video)
        rewind_button.grid(row=7, column=1, pady=5)

        select_button = Button(self.root, text="Select Video", command=self.select_video)
        select_button.grid(row=7, column=2, pady=5)

        apply_changes_button = Button(self.root, text="Apply Changes", command=self.apply_changes)
        apply_changes_button.grid(row=7, column=3, pady=5)

        # Button for exporting settings
        export_settings_button = Button(self.root, text="Export Settings", command=self.export_settings_wrapper)
        export_settings_button.grid(row=10, column=1, pady=5)

        # Button for importing settings
        import_settings_button = Button(self.root, text="Import Settings", command=self.import_settings_wrapper)
        import_settings_button.grid(row=10, column=0, pady=5)

    def create_resolution_fields(self):
        resolution_label = Label(self.root, text="Output Res/Scale:")
        resolution_label.grid(row=8, column=0, pady=5)

        self.resolution_width_entry = Entry(self.root)
        self.resolution_width_entry.insert(0, str(self.output_width))
        self.resolution_width_entry.grid(row=8, column=1, pady=5)

        x_label = Label(self.root, text="x")
        x_label.grid(row=8, column=2, pady=1)

        self.resolution_height_entry = Entry(self.root)
        self.resolution_height_entry.insert(0, str(self.output_height))
        self.resolution_height_entry.grid(row=8, column=3, pady=5)

    def toggle_pause(self):
        self.paused = not self.paused

    def rewind_video(self):
        if self.cap is not None:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def select_video(self):
        new_video_path = filedialog.askopenfilename(title="Select Video File", filetypes=[("Video files", "*.mp4;*.avi")])
        if new_video_path:
            self.video_path = new_video_path
            self.cap = cv2.VideoCapture(self.video_path)
            if not self.cap.isOpened():
                print("Error: Unable to open video.")
                self.video_path = None
                self.cap = None
                return
            self.paused = False

    def apply_changes(self):
        self.update_src_points()
        self.update_resolution()
        self.update_speed()
        self.update_opacity()
        self.update_rotation()

        # If the video is not paused, update the transformation immediately
        if self.cap is not None and not self.paused:
            ret, frame = self.cap.read()
            if ret:
                self.M = cv2.getPerspectiveTransform(self.src_points, self.dst_points)
                self.display_transformed_frame(frame)

    def export_settings(self, file_path):
        settings = {
            'src_points': self.src_points.tolist(),
            'output_width': self.output_width,
            'output_height': self.output_height,
            'speed': self.speed,
            'opacity': self.opacity_scale.get(),
            'rotation_angle': self.rotation_angle,
        }

        with open(file_path, 'w') as json_file:
            json.dump(settings, json_file)

    def import_settings(self, file_path):
        try:
            with open(file_path, 'r') as json_file:
                settings = json.load(json_file)

            self.src_points = np.array(settings['src_points'], dtype=np.float32)
            self.output_width = settings['output_width']
            self.output_height = settings['output_height']
            self.speed = settings['speed']
            self.opacity = settings['opacity']
            self.rotation_angle = settings['rotation_angle']

            # Update GUI with the imported settings
            self.update_gui_with_settings()

            print("Settings imported successfully.")
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Error importing settings: {e}")

    def update_gui_with_settings(self):
        # Update entry fields with imported settings
        for i in range(4):
            self.entry_fields[2 * i].delete(0, tk.END)
            self.entry_fields[2 * i].insert(0, str(self.src_points[i, 0]))

            self.entry_fields[2 * i + 1].delete(0, tk.END)
            self.entry_fields[2 * i + 1].insert(0, str(self.src_points[i, 1]))

        self.resolution_width_entry.delete(0, tk.END)
        self.resolution_width_entry.insert(0, str(self.output_width))

        self.resolution_height_entry.delete(0, tk.END)
        self.resolution_height_entry.insert(0, str(self.output_height))

        self.speed_entry.delete(0, tk.END)
        self.speed_entry.insert(0, str(self.speed))

        self.opacity_scale.set(self.opacity)

        self.rotation_entry.delete(0, tk.END)
        self.rotation_entry.insert(0, str(self.rotation_angle))

    def update_speed(self):
        try:
            self.speed = min(float(self.speed_entry.get()), 1.0)
        except ValueError:
            print("Invalid speed value. Please enter a valid floating-point number.")

    def update_src_points(self):
        try:
            for i in range(4):
                self.src_points[i, 0] = float(self.entry_fields[2 * i].get())
                self.src_points[i, 1] = float(self.entry_fields[2 * i + 1].get())

            self.M = cv2.getPerspectiveTransform(self.src_points, self.dst_points)

        except ValueError:
            print("Invalid coordinate value. Please enter valid floating-point numbers.")

    def update_resolution(self):
        try:
            self.output_width = max(int(self.resolution_width_entry.get()), 1)
            self.output_height = max(int(self.resolution_height_entry.get()), 1)
        except ValueError:
            print("Invalid resolution value. Please enter valid integer values.")

    def update_opacity(self):
        self.opacity = self.opacity_scale.get()

    def update_rotation(self):
        try:
            self.rotation_angle = float(self.rotation_entry.get())
        except ValueError:
            print("Invalid rotation value. Please enter a valid floating-point number.")

    def process_video(self):
        if self.cap is not None and not self.paused:
            ret, frame = self.cap.read()

            if not ret:
                self.cap.release()
                cv2.destroyAllWindows()
                return

            self.display_transformed_frame(frame)

            # Control playback speed
            delay = int(1000 / self.cap.get(cv2.CAP_PROP_FPS) / self.speed)

            key = cv2.waitKey(delay) & 0xFF

            if key == 27:  # Esc key to exit
                self.cap.release()
                cv2.destroyAllWindows()
            else:
                self.root.after(1, self.process_video)
        else:
            # If paused or no video is loaded, continue waiting for user actions
            self.root.after(100, self.process_video)

    def display_transformed_frame(self, frame):
        transformed_frame = cv2.warpPerspective(frame, self.M, (self.output_width, self.output_height))
        rotated_frame = self.rotate_frame(transformed_frame, self.rotation_angle)
        resized_overlay = cv2.resize(self.overlay_image, (rotated_frame.shape[1], rotated_frame.shape[0]))
        overlay = cv2.addWeighted(rotated_frame, 1 - self.opacity, resized_overlay, self.opacity, 0)

        cv2.imshow("Original Video", frame)
        cv2.imshow("Transformed Video with Overlay", overlay)

    def rotate_frame(self, frame, angle):
        center = (frame.shape[1] // 2, frame.shape[0] // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated_frame = cv2.warpAffine(frame, rotation_matrix, (frame.shape[1], frame.shape[0]))
        return rotated_frame

    def export_settings_wrapper(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            self.export_settings(file_path)

    def import_settings_wrapper(self):
        file_path = filedialog.askopenfilename(title="Select Settings File", filetypes=[("JSON files", "*.json")])
        if file_path:
            self.import_settings(file_path)

    def adjust_offset(self, x_offset, y_offset):
        try:
            for i in range(4):
                self.src_points[i, 0] += x_offset
                self.src_points[i, 1] += y_offset

            # Update the transformation matrix
            self.M = cv2.getPerspectiveTransform(self.src_points, self.dst_points)

            # Update the GUI with the adjusted coordinates
            self.update_gui_with_settings()

            # If the video is not paused, update the transformation immediately
            if self.cap is not None:
                ret, frame = self.cap.read()
                if ret:
                    self.display_transformed_frame(frame)

        except ValueError:
            print("Invalid coordinate value. Please enter valid floating-point numbers.")

# Create an instance of VideoProcessor
video_processor = VideoProcessor()