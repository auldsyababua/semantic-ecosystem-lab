"""Main entry point for Office Assistant MVP."""
import tkinter as tk
from tkinter import messagebox
import sys
from .gui import OfficeAssistantGUI


def main():
    """Initialize and run the Office Assistant application."""
    try:
        # Create root window
        root = tk.Tk()

        # Create GUI
        app = OfficeAssistantGUI(root)

        # Start main loop
        root.mainloop()

    except Exception as e:
        messagebox.showerror("Startup Error", f"Failed to start application:\n{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
