import tkinter as tk
from src.UI.components.game_background import GameBackground


class GameScreen:
    def __init__(self, root, bg_image_path="resources/textures/game_show_background.png"):
        self.root = root

        self._setup_display()

        # Create canvas
        self.canvas = tk.Canvas(root, highlightthickness=0, bg="black")
        self.canvas.pack(fill="both", expand=True)

        # Initialize background
        self.background = GameBackground(self.canvas, bg_image_path)

        # # Setup UI
        # self.setup_ui()

        # Bind escape key
        self.root.bind("<Escape>", lambda e: self.root.destroy())

    def _setup_display(self):

        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Set geometry first (windowed fullscreen)
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")

        # Then set fullscreen attribute
        self.root.attributes("-fullscreen", True)

        # Remove window decorations (title bar, borders)
        self.root.overrideredirect(False)  # Must be False when using fullscreen

        # Make sure window stays on top
        self.root.attributes("-topmost", True)

    def setup_ui(self):
        """Add UI elements"""
        # Score display
        self.score = 0
        self.score_label = tk.Label(
            self.canvas,
            text=f"Score: {self.score}",
            font=("Arial", 24),
            bg="black",
            fg="white"
        )
        self.canvas.create_window(50, 50, window=self.score_label, anchor="nw")

        # Main button
        self.action_button = tk.Button(
            self.canvas,
            text="Start Game",
            command=self.start_game,
            font=("Arial", 18),
            bg="green",
            fg="white"
        )
        self.canvas.create_window(
            self.root.winfo_screenwidth() // 2,
            self.root.winfo_screenheight() // 2,
            window=self.action_button,
            anchor="center"
        )

    def start_game(self):
        self.score += 100
        self.score_label.config(text=f"Score: {self.score}")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    app = GameScreen(root)
    app.run()