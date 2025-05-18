import tkinter as tk
from tkinter import ttk


class SettingsWidget:
    def __init__(self, game_screen, canvas):
        self.game_screen = game_screen
        self.canvas = canvas

        # Create settings frame
        self.frame = tk.Frame(canvas, bg="#333333", bd=1, relief="solid")
        self._setup_ui()

        # Settings toggle button
        self.toggle_button = tk.Button(
            canvas,
            text="⚙",
            command=self.toggle_visibility,
            font=("Arial", 14),
            bg="#444444",
            fg="white",
            bd=0
        )

        # Add widgets using game screen's method
        self.button_id = game_screen.add_widget(
            self.toggle_button,
            game_screen.screen_width - 30,
            10,
            anchor='ne'
        )

        self.frame_id = game_screen.add_widget(
            self.frame,
            game_screen.screen_width - 10,
            50,
            anchor='ne'
        )

        self.visible = False
        self.canvas.itemconfigure(self.frame_id, state='hidden')

    def _setup_ui(self):
        """Create settings controls"""
        # Title
        tk.Label(
            self.frame,
            text="Settings",
            bg="#333333",
            fg="white",
            font=("Arial", 10, "bold")
        ).pack(pady=(5, 10))

        # Display mode
        self.display_mode = tk.StringVar(value="fullscreen")

        modes = [
            ("Fullscreen", "fullscreen"),
            ("Windowed Fullscreen", "windowed")
        ]

        for text, mode in modes:
            rb = tk.Radiobutton(
                self.frame,
                text=text,
                variable=self.display_mode,
                value=mode,
                command=self._update_display_mode,
                bg="#333333",
                fg="white",
                selectcolor="#222222"
            )
            rb.pack(anchor="w", padx=5)

    def _update_display_mode(self):
        """Handle display mode changes without split screen"""
        mode = self.display_mode.get()
        root = self.game_screen.root

        if mode == "fullscreen":
            root.attributes("-fullscreen", True)
            root.geometry("")  # Clear any window geometry
            root.overrideredirect(False)
        else:
            root.attributes("-fullscreen", False)
            root.overrideredirect(True)
            # Get actual screen dimensions (works across multi-monitor setups)
            root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")

    def toggle_visibility(self):
        """Toggle settings panel visibility"""
        if self.visible:
            self.canvas.itemconfigure(self.frame_id, state='hidden')
            self.toggle_button.config(text="⚙")
        else:
            self.canvas.itemconfigure(self.frame_id, state='normal')
            self.toggle_button.config(text="×")
        self.visible = not self.visible