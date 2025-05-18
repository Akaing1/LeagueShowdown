import tkinter as tk
from PIL import Image, ImageTk


class GameBackground:
    def __init__(self, canvas, image_path):
        self.canvas = canvas
        self.image_path = image_path
        self.bg_image = None
        self.original_image = None

        # Load image immediately
        self.load_image()

        # Set up resize binding
        self.canvas.bind("<Configure>", self.resize_background)

    def load_image(self):
        """Load and initially display the background image"""
        try:
            self.original_image = Image.open(self.image_path)
            self.resize_background()
        except Exception as e:
            print(f"Error loading background: {e}")
            self.show_error_message()

    def resize_background(self, event=None):
        """Resize image to fit canvas while maintaining aspect ratio"""
        if not self.original_image:
            return

        try:
            # Get current canvas size
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            # Skip if canvas isn't ready
            if canvas_width <= 1 or canvas_height <= 1:
                return

            # Calculate new dimensions maintaining aspect ratio
            img_ratio = self.original_image.width / self.original_image.height
            canvas_ratio = canvas_width / canvas_height

            if img_ratio > canvas_ratio:
                # Fit to width
                new_width = canvas_width
                new_height = int(canvas_width / img_ratio)
            else:
                # Fit to height
                new_height = canvas_height
                new_width = int(canvas_height * img_ratio)

            # Resize and update
            resized_img = self.original_image.resize((new_width, new_height), Image.LANCZOS)
            self.bg_image = ImageTk.PhotoImage(resized_img)

            # Update canvas
            self.canvas.delete("background")
            self.canvas.create_image(
                canvas_width // 2, canvas_height // 2,
                image=self.bg_image,
                tags="background"
            )
            self.canvas.tag_lower("background")

        except Exception as e:
            print(f"Error resizing background: {e}")
            self.show_error_message()

    def show_error_message(self):
        """Display error message if background fails to load"""
        self.canvas.config(bg="black")
        error_msg = tk.Label(
            self.canvas,
            text="Background image missing!",
            fg="white", bg="black",
            font=("Arial", 24)
        )
        self.canvas.create_window(
            self.canvas.winfo_width() // 2,
            self.canvas.winfo_height() // 2,
            window=error_msg,
            anchor="center"
        )