import customtkinter as ctk
from tkinter import messagebox
import sqlite3
from datetime import date, timedelta
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

DB_FILE = "data/expenses.db"

class FinanceTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Finance Tracker")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        if not os.path.exists("data"):
            os.makedirs("data")
        self.conn = sqlite3.connect(DB_FILE)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        self.conn.commit()

        self.selected_expense_id = None
        self.selected_label = None

        self.setup_ui()
        self.load_expenses()
        self.update_summary()

    def setup_ui(self):
        font_large = ("Helvetica Neue", 16)

        input_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        input_frame.pack(fill="x", padx=20, pady=15)

        self.amount_entry = ctk.CTkEntry(
            input_frame, placeholder_text="Amount", font=font_large, height=40
        )
        self.amount_entry.grid(row=0, column=0, padx=6, pady=6, sticky="ew")
        self.amount_entry.bind("<FocusOut>", self.format_amount)

        self.category_var = ctk.StringVar()
        self.category_menu = ctk.CTkComboBox(
            input_frame,
            values=["Food", "Transport", "Utilities", "Health", "Entertainment", "Shopping", "Education", "Other"],
            variable=self.category_var, font=font_large, height=40
        )
        self.category_menu.set("Select Category")
        self.category_menu.grid(row=0, column=1, padx=6, pady=6, sticky="ew")

        today = date.today()
        years = [str(y) for y in range(today.year - 5, today.year + 1)]
        months = [str(m) for m in range(1, 13)]
        days = [str(d) for d in range(1, 32)]

        self.year_var = ctk.StringVar(value=str(today.year))
        self.month_var = ctk.StringVar(value=str(today.month))
        self.day_var = ctk.StringVar(value=str(today.day))

        self.year_menu = ctk.CTkComboBox(input_frame, values=years, variable=self.year_var, font=font_large, height=40)
        self.month_menu = ctk.CTkComboBox(input_frame, values=months, variable=self.month_var, font=font_large, height=40)
        self.day_menu = ctk.CTkComboBox(input_frame, values=days, variable=self.day_var, font=font_large, height=40)
        self.year_menu.grid(row=0, column=2, padx=4)
        self.month_menu.grid(row=0, column=3, padx=4)
        self.day_menu.grid(row=0, column=4, padx=4)

        self.add_button = ctk.CTkButton(input_frame, text="Add Expense", command=self.add_expense, font=font_large, height=40)
        self.update_button = ctk.CTkButton(input_frame, text="Update", command=self.update_expense, font=font_large, height=40)
        self.delete_button = ctk.CTkButton(input_frame, text="Delete", command=self.delete_expense, fg_color="red", font=font_large, height=40)

        self.add_button.grid(row=0, column=5, padx=8)
        self.update_button.grid(row=0, column=6, padx=8)
        self.delete_button.grid(row=0, column=7, padx=8)
        self.update_button.grid_remove()
        self.delete_button.grid_remove()

        for i in range(8):
            input_frame.grid_columnconfigure(i, weight=1)

        settings_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        settings_frame.pack(fill="x", padx=20, pady=10)

        self.limit_var = ctk.StringVar()
        self.limit_entry = ctk.CTkEntry(settings_frame, placeholder_text="Set Monthly Limit", textvariable=self.limit_var, font=font_large, height=10)
        self.limit_entry.pack(side="left", padx=(0, 5), fill="x", expand=True)
        self.limit_save_btn = ctk.CTkButton(settings_frame, text="Save Limit", command=self.save_limit, font=font_large, height=40)
        self.limit_save_btn.pack(side="left")

        self.tree_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.tree_frame.pack(fill="both", expand=False, padx=20, pady=5)
        self.tree_labels = []

        self.summary_label = ctk.CTkLabel(self.root, text="", font=("Helvetica Neue", 18, "bold"))
        self.summary_label.pack(pady=10)

        self.chart_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.chart_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.load_limit()

    def format_amount(self, event):
        val = self.amount_entry.get().replace(",", "")
        if val.replace('.', '', 1).isdigit():
            self.amount_entry.delete(0, "end")
            self.amount_entry.insert(0, f"{float(val):,.2f}")

    def get_date(self):
        try:
            y, m, d = int(self.year_var.get()), int(self.month_var.get()), int(self.day_var.get())
            return date(y, m, d)
        except:
            return None

    def add_expense(self):
        dt = self.get_date()
        if not dt or dt < date.today():
            messagebox.showerror("Invalid Date", "Cannot add past dates.")
            return
        try:
            amt = float(self.amount_entry.get().replace(",", ""))
            cat = self.category_var.get()
        except:
            messagebox.showerror("Invalid Input", "Enter a valid amount.")
            return

        self.cursor.execute("INSERT INTO expenses(amount,category,date) VALUES(?,?,?)", (amt, cat, dt.isoformat()))
        self.conn.commit()
        self.reset_inputs()
        self.load_expenses()
        self.update_summary()

    def update_expense(self):
        if not self.selected_expense_id:
            return
        dt = self.get_date()
        if not dt or dt < date.today():
            messagebox.showerror("Invalid Date", "Cannot use past date.")
            return
        try:
            amt = float(self.amount_entry.get().replace(",", ""))
            cat = self.category_var.get()
        except:
            messagebox.showerror("Invalid Input", "Enter a valid amount.")
            return

        self.cursor.execute("UPDATE expenses SET amount=?,category=?,date=? WHERE id=?", (amt, cat, dt.isoformat(), self.selected_expense_id))
        self.conn.commit()
        self.reset_inputs()
        self.load_expenses()
        self.update_summary()

    def delete_expense(self):
        if not self.selected_expense_id:
            return
        self.cursor.execute("DELETE FROM expenses WHERE id=?", (self.selected_expense_id,))
        self.conn.commit()
        self.reset_inputs()
        self.load_expenses()
        self.update_summary()

    def reset_inputs(self):
        self.amount_entry.delete(0, "end")
        self.category_menu.set("Select Category")
        today = date.today()
        self.year_var.set(str(today.year))
        self.month_var.set(str(today.month))
        self.day_var.set(str(today.day))
        if self.selected_label:
            self.selected_label.configure(bg_color="transparent")
        self.selected_label = None
        self.selected_expense_id = None
        self.update_button.grid_remove()
        self.delete_button.grid_remove()

    def on_row_selected(self, eid, amt, cat, dt_str, label):
        if self.selected_expense_id == eid:
            self.reset_inputs()
            return
        if self.selected_label:
            self.selected_label.configure(bg_color="transparent")
        self.selected_expense_id = eid
        self.selected_label = label
        label.configure(bg_color="gray30")
        self.amount_entry.delete(0, "end")
        self.amount_entry.insert(0, f"{amt:,.2f}")
        self.category_menu.set(cat)
        y, m, d = map(int, dt_str.split("-"))
        self.year_var.set(str(y))
        self.month_var.set(str(m))
        self.day_var.set(str(d))
        self.update_button.grid()
        self.delete_button.grid()

    def load_expenses(self):
        for w in self.tree_labels:
            w.destroy()
        self.tree_labels.clear()
        self.cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
        for eid, amt, cat, dt in self.cursor.fetchall():
            txt = f"{eid} | ${amt:,.2f} | {cat} | {dt}"
            lbl = ctk.CTkLabel(self.tree_frame, text=txt, font=("Helvetica Neue", 14))
            lbl.pack(fill="x", padx=5, pady=2)
            lbl.bind("<Button-1>", lambda e, i=eid, a=amt, c=cat, d=dt, l=lbl: self.on_row_selected(i, a, c, d, l))
            self.tree_labels.append(lbl)

    def load_limit(self):
        self.cursor.execute("SELECT value FROM settings WHERE key='monthly_limit'")
        row = self.cursor.fetchone()
        if row:
            self.limit_var.set(row[0])

    def save_limit(self):
        try:
            limit_val = float(self.limit_var.get().replace(",", ""))
            self.cursor.execute("REPLACE INTO settings(key, value) VALUES('monthly_limit', ?)", (str(limit_val),))
            self.conn.commit()
            self.update_summary()
        except:
            messagebox.showerror("Invalid Input", "Please enter a valid number for limit.")

    def update_summary(self):
        self.cursor.execute("SELECT value FROM settings WHERE key='monthly_limit'")
        row = self.cursor.fetchone()
        limit = float(row[0]) if row else 0
        self.cursor.execute("SELECT SUM(amount) FROM expenses WHERE strftime('%Y-%m', date) = ?", (date.today().strftime('%Y-%m'),))
        total = self.cursor.fetchone()[0] or 0.0
        if limit and total > limit:
            self.summary_label.configure(text=f"Total Spent: ${total:,.2f} (Over Limit!)", text_color="red")
        else:
            self.summary_label.configure(text=f"Total Spent: ${total:,.2f}", text_color="green")
        self.draw_charts()

    def draw_charts(self):
        for w in self.chart_frame.winfo_children():
            w.destroy()

        today = date.today()
        frames = [("Today", today), ("This Week", today - timedelta(days=7)), ("This Month", today.replace(day=1))]

        self.cursor.execute("SELECT date, SUM(amount) FROM expenses GROUP BY date")
        rows = self.cursor.fetchall()
        monthly = {}
        for dt_str, amt in rows:
            dt = date.fromisoformat(dt_str)
            if dt.year == today.year:
                monthly.setdefault(dt.month, 0)
                monthly[dt.month] += amt

        fig = plt.figure(figsize=(12, 8), dpi=100)
        gs = fig.add_gridspec(2, 3, height_ratios=[1, 1.2], hspace=0.4)

        for i, (label, start) in enumerate(frames):
            ax = fig.add_subplot(gs[0, i])
            self.cursor.execute("SELECT category, SUM(amount) FROM expenses WHERE date>=? GROUP BY category", (start.isoformat(),))
            data = self.cursor.fetchall()
            if data:
                cats, amts = zip(*data)
                wedges, texts, autotexts = ax.pie(amts, labels=cats, autopct='%1.1f%%', startangle=90,
                                                  wedgeprops=dict(width=0.4))
                ax.legend(wedges, cats, loc="center left", bbox_to_anchor=(1, 0.5))
                total_amt = sum(amts)
                ax.set_title(f"{label}\n${total_amt:,.2f}", fontsize=14)

        ax2 = fig.add_subplot(gs[1, :])
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        values = [monthly.get(m, 0) for m in range(1, 13)]
        avg_val = np.mean(values) if values else 0

        ax2.plot(months, values, marker='o', linestyle='-', color='tab:blue', linewidth=2)
        ax2.axhline(avg_val, color='orange', linestyle='--', label=f"Average: ${avg_val:,.0f}")
        ax2.set_title("Yearly Expense Trend", fontsize=16)
        ax2.set_ylabel("Total Spent", fontsize=14)
        ax2.legend()
        ax2.grid(True, linestyle='--', alpha=0.5)

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

def show_main_app():
    splash.destroy()
    root = ctk.CTk()
    app = FinanceTracker(root)
    root.mainloop()

if __name__ == "__main__":
    splash = ctk.CTk()
    splash.title("Loading...")
    splash.geometry("400x300")
    splash.resizable(False, False)

    label = ctk.CTkLabel(splash, text="Loading Finance Tracker...", font=("Helvetica Neue", 20, "bold"))
    label.pack(expand=True)

    splash.after(5000, show_main_app)
    splash.mainloop()

