import tkinter as tk
from tkinter import messagebox, Toplevel
from PIL import Image, ImageTk
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
from playsound import playsound
import threading

# ---------------- DATABASE ---------------- #

conn = sqlite3.connect("coffee_sales.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coffee_name TEXT,
    amount INTEGER,
    date_time TEXT
)
""")
conn.commit()

# ---------------- CLASSES ---------------- #

class MenuItem:
    def __init__(self, name, water, milk, coffee, cost):
        self.name = name
        self.ingredients = {
            "water": water,
            "milk": milk,
            "coffee": coffee
        }
        self.cost = cost


class CoffeeMachine:
    def __init__(self):
        self.resources = {
            "water": 1000,
            "milk": 500,
            "coffee": 300
        }

    def is_resource_sufficient(self, menu_item):
        for item in menu_item.ingredients:
            if menu_item.ingredients[item] > self.resources.get(item, 0):
                return False
        return True

    def make_coffee(self, menu_item):
        for item in menu_item.ingredients:
            self.resources[item] -= menu_item.ingredients[item]

    def refill(self):
        self.resources = {
            "water": 1000,
            "milk": 500,
            "coffee": 300
        }
        update_resources_display()
        messagebox.showinfo("Refill", "Resources Refilled Successfully!")


class Payment:
    def process_payment(self, amount_given, cost):
        if amount_given >= cost:
            return True, amount_given - cost
        return False, 0


class TransactionManager:
    def save_transaction(self, coffee_name, amount):
        cursor.execute("""
        INSERT INTO transactions (coffee_name, amount, date_time)
        VALUES (?, ?, ?)
        """, (coffee_name, amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()

    def get_total_sales(self):
        cursor.execute("SELECT SUM(amount) FROM transactions")
        result = cursor.fetchone()[0]
        return result if result else 0

    def get_daily_sales(self):
        cursor.execute("""
        SELECT DATE(date_time), SUM(amount)
        FROM transactions
        GROUP BY DATE(date_time)
        """)
        return cursor.fetchall()


# ---------------- MENU ITEMS ---------------- #

latte = MenuItem("Latte", 200, 150, 24, 150)
espresso = MenuItem("Espresso", 50, 0, 18, 100)
cappuccino = MenuItem("Cappuccino", 250, 100, 24, 200)

# ---------------- FUNCTIONS ---------------- #

def play_sound():
    try:
        playsound("coffee.wav")
    except:
        pass

def order_coffee(menu_item):
    try:
        amount_given = int(entry_amount.get())
    except ValueError:
        messagebox.showerror("Error", "Enter valid amount")
        return

    if not machine.is_resource_sufficient(menu_item):
        messagebox.showerror("Error", "Not enough resources!")
        return

    payment = Payment()
    success, change = payment.process_payment(amount_given, menu_item.cost)

    if success:
        machine.make_coffee(menu_item)
        update_resources_display()

        transaction = TransactionManager()
        transaction.save_transaction(menu_item.name, menu_item.cost)

        threading.Thread(target=play_sound).start()

        messagebox.showinfo(
            "Enjoy ☕",
            f"Here is your {menu_item.name}!\nChange: ₹{change}"
        )
        entry_amount.delete(0, tk.END)
    else:
        messagebox.showerror("Error", "Not enough money!")


def update_resources_display():
    resource_label.config(
        text=f"Water: {machine.resources['water']} ml | "
             f"Milk: {machine.resources['milk']} ml | "
             f"Coffee: {machine.resources['coffee']} g"
    )


def show_sales_chart():
    transaction = TransactionManager()
    data = transaction.get_daily_sales()

    if not data:
        messagebox.showinfo("Info", "No sales data available.")
        return

    dates = [row[0] for row in data]
    sales = [row[1] for row in data]

    plt.figure()
    plt.bar(dates, sales)
    plt.title("Daily Sales Report")
    plt.xlabel("Date")
    plt.ylabel("Sales (₹)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def admin_popup():
    popup = Toplevel(root)
    popup.title("Admin Login")
    popup.geometry("300x200")

    tk.Label(popup, text="Enter Password:", font=("Arial", 12)).pack(pady=10)
    entry = tk.Entry(popup, show="*")
    entry.pack(pady=5)

    def check():
        if entry.get() == "admin123":
            popup.destroy()
            show_sales_chart()
        else:
            messagebox.showerror("Error", "Wrong Password")

    tk.Button(popup, text="Login", command=check).pack(pady=10)


def on_enter(e):
    e.widget["background"] = "#8b5a2b"

def on_leave(e):
    e.widget["background"] = "#6f4e37"


# ---------------- MAIN WINDOW ---------------- #

machine = CoffeeMachine()

root = tk.Tk()
root.title("Smart Coffee Shop Pro")
root.geometry("550x720")
root.configure(bg="#ede0d4")

# Image
try:
    img = Image.open("coffee.png")
    img = img.resize((280, 280))
    coffee_img = ImageTk.PhotoImage(img)

    frame = tk.Frame(root, bg="#d7b899", bd=6, relief="ridge")
    frame.pack(pady=20)
    tk.Label(frame, image=coffee_img, bg="#d7b899").pack()
except:
    pass

tk.Label(root, text="☕ Smart Coffee Machine ☕",
         font=("Helvetica", 20, "bold"),
         bg="#ede0d4", fg="#4b2e2e").pack(pady=10)

tk.Label(root, text="Enter Amount (₹):",
         bg="#ede0d4", font=("Arial", 13)).pack()

entry_amount = tk.Entry(root, font=("Arial", 13), justify="center")
entry_amount.pack(pady=8)

button_style = {
    "width": 28,
    "height": 2,
    "font": ("Arial", 11, "bold"),
    "bg": "#6f4e37",
    "fg": "white",
    "bd": 0
}

buttons = [
    tk.Button(root, text="Order Latte (₹150)",
              command=lambda: order_coffee(latte), **button_style),
    tk.Button(root, text="Order Espresso (₹100)",
              command=lambda: order_coffee(espresso), **button_style),
    tk.Button(root, text="Order Cappuccino (₹200)",
              command=lambda: order_coffee(cappuccino), **button_style)
]

for btn in buttons:
    btn.pack(pady=6)
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)

resource_label = tk.Label(root,
                          bg="#ede0d4",
                          font=("Arial", 12),
                          fg="#3e2723")
resource_label.pack(pady=15)

update_resources_display()

tk.Button(root, text="Admin Panel",
          command=admin_popup,
          bg="#3e2723", fg="white",
          width=20).pack(pady=6)

tk.Button(root, text="Refill Resources",
          command=machine.refill,
          bg="#2e7d32", fg="white",
          width=20).pack(pady=6)

root.mainloop()