# main.py
import customtkinter as ctk
from ui import FinanceTracker
from database import init_db

def show_main_app():
    splash.destroy()
    root = ctk.CTk()
    app = FinanceTracker(root)
    root.mainloop()

if __name__ == "__main__":
    init_db()

    splash = ctk.CTk()
    splash.title("Loading...")
    splash.geometry("400x300")
    splash.resizable(False, False)

    label = ctk.CTkLabel(splash, text="Loading Finance Tracker...", font=("Helvetica Neue", 20, "bold"))
    label.pack(expand=True)

    splash.after(3000, show_main_app)
    splash.mainloop()
