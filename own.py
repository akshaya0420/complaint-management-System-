import mysql.connector
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
import bcrypt
import re

# Establish MySQL connection
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",  # Replace with your MySQL username
        password="2004",  # Replace with your MySQL password
        database="university_complaints_db"  # Replace with your database name
      
        
    )
    cursor = db.cursor()
except mysql.connector.Error as err:
    print(f"Error: {err}")
    exit(1)

# Global variable for the logged-in user
logged_in_user = None

# Main Tkinter window
root = tk.Tk()
root.title("Complaint Management System")
root.geometry("600x500")
root.config(bg="#f0f0f0")

# Custom styles for buttons and labels
button_style = {'font': ('Helvetica', 12), 'bg': '#4CAF50', 'fg': 'white', 'bd': 0, 'width': 20, 'pady': 5}
label_style = {'font': ('Helvetica', 14), 'bg': '#f0f0f0', 'fg': '#333'}
input_style = {'font': ('Helvetica', 12), 'width': 30}

# Logout function
def logout():
    global logged_in_user
    logged_in_user = None
    for widget in root.winfo_children():
        widget.pack_forget()
    main_interface()

# Signup function with validation
def signup():
    def register_user():
        username = entry_username.get()
        email = entry_email.get()
        password = entry_password.get().encode('utf-8')
        confirm_password = entry_confirm_password.get().encode('utf-8')

        # Email validation
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messagebox.showerror("Error", "Invalid email format.")
            return

        # Password strength validation
        if len(password) < 8 or not re.search(r'[A-Za-z]', password.decode('utf-8')) or not re.search(r'\d', password.decode('utf-8')):
            messagebox.showerror("Error", "Password must be at least 8 characters long, with letters and numbers.")
            return

        # Password match validation
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match.")
            return

        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

        try:
            cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, hashed_password))
            db.commit()
            messagebox.showinfo("Success", "User registered successfully!")
            signup_window.destroy()
        except mysql.connector.IntegrityError:
            messagebox.showerror("Error", "Username or email already exists.")
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Failed to register user: {err}")

    signup_window = tk.Toplevel(root)
    signup_window.title("Signup")
    signup_window.geometry("400x400")
    signup_window.config(bg="#f0f0f0")

    tk.Label(signup_window, text="Username", **label_style).pack(pady=10)
    entry_username = tk.Entry(signup_window, **input_style)
    entry_username.pack(pady=5)

    tk.Label(signup_window, text="Email", **label_style).pack(pady=10)
    entry_email = tk.Entry(signup_window, **input_style)
    entry_email.pack(pady=5)

    tk.Label(signup_window, text="Password", **label_style).pack(pady=10)
    entry_password = tk.Entry(signup_window, show="*", **input_style)
    entry_password.pack(pady=5)

    tk.Label(signup_window, text="Confirm Password", **label_style).pack(pady=10)
    entry_confirm_password = tk.Entry(signup_window, show="*", **input_style)
    entry_confirm_password.pack(pady=5)

    tk.Button(signup_window, text="Signup", **button_style, command=register_user).pack(pady=20)

# Add complaint function
def add_complaint():
    def submit_complaint():
        name = entry_name.get()
        department = entry_department.get()
        complaint_text = entry_complaint.get()

        if name and department and complaint_text:
            cursor.execute("SELECT id FROM users WHERE username=%s", (logged_in_user,))
            user_id = cursor.fetchone()[0]
            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("INSERT INTO complaints (user_id, name, department, complaint, date) VALUES (%s, %s, %s, %s, %s)", 
                           (user_id, name, department, complaint_text, date))
            db.commit()
            messagebox.showinfo("Success", "Complaint registered successfully!")
            complaint_window.destroy()
        else:
            messagebox.showwarning("Input Error", "Please fill in all fields.")

    complaint_window = tk.Toplevel(root)
    complaint_window.title("Register Complaint")
    complaint_window.geometry("400x400")
    complaint_window.config(bg="#f0f0f0")

    tk.Label(complaint_window, text="Name", **label_style).pack(pady=10)
    entry_name = tk.Entry(complaint_window, **input_style)
    entry_name.pack(pady=5)

    tk.Label(complaint_window, text="Department", **label_style).pack(pady=10)
    entry_department = tk.Entry(complaint_window, **input_style)
    entry_department.pack(pady=5)

    tk.Label(complaint_window, text="Complaint Description", **label_style).pack(pady=10)
    entry_complaint = tk.Entry(complaint_window, **input_style)
    entry_complaint.pack(pady=5)

    tk.Button(complaint_window, text="Submit", **button_style, command=submit_complaint).pack(pady=20)

# View complaints function
def view_complaints():
    def show_complaints():
        cursor.execute("SELECT * FROM complaints WHERE user_id=(SELECT id FROM users WHERE username=%s)", (logged_in_user,))
        complaints = cursor.fetchall()

        if complaints:
            complaint_texts = [f"Complaint ID: {c[0]}\nName: {c[2]}\nDepartment: {c[3]}\nComplaint: {c[4]}\nDate: {c[5]}" for c in complaints]
            messagebox.showinfo("Your Complaints", "\n\n".join(complaint_texts))
        else:
            messagebox.showinfo("No Complaints", "You have not registered any complaints yet.")

    show_complaints()

# Withdraw complaint function
def withdraw_complaint():
    def remove_complaint():
        complaint_id = entry_complaint_id.get()
        cursor.execute("DELETE FROM complaints WHERE id=%s AND user_id=(SELECT id FROM users WHERE username=%s)", (complaint_id, logged_in_user))
        db.commit()
        messagebox.showinfo("Success", "Complaint withdrawn successfully!")
        withdraw_window.destroy()

    withdraw_window = tk.Toplevel(root)
    withdraw_window.title("Withdraw Complaint")
    withdraw_window.geometry("400x300")
    withdraw_window.config(bg="#f0f0f0")

    tk.Label(withdraw_window, text="Complaint ID", **label_style).pack(pady=10)
    entry_complaint_id = tk.Entry(withdraw_window, **input_style)
    entry_complaint_id.pack(pady=5)

    tk.Button(withdraw_window, text="Withdraw", **button_style, command=remove_complaint).pack(pady=20)

# Login function with error handling
def login():
    def verify_user():
        global logged_in_user
        username = entry_username.get()
        password = entry_password.get().encode('utf-8')

        cursor.execute("SELECT password FROM users WHERE username=%s", (username,))
        result = cursor.fetchone()
        if result and bcrypt.checkpw(password, result[0].encode('utf-8')):
            messagebox.showinfo("Success", "Login successful!")
            logged_in_user = username
            login_window.destroy()
            main_interface()
        else:
            messagebox.showerror("Error", "Invalid username or password")

    login_window = tk.Toplevel(root)
    login_window.title("Login")
    login_window.geometry("400x300")
    login_window.config(bg="#f0f0f0")

    tk.Label(login_window, text="Username", **label_style).pack(pady=10)
    entry_username = tk.Entry(login_window, **input_style)
    entry_username.pack(pady=5)

    tk.Label(login_window, text="Password", **label_style).pack(pady=10)
    entry_password = tk.Entry(login_window, show="*", **input_style)
    entry_password.pack(pady=5)

    tk.Button(login_window, text="Login", **button_style, command=verify_user).pack(pady=20)

# Main user interface
def main_interface():
    for widget in root.winfo_children():
        widget.pack_forget()

    if logged_in_user:
        tk.Label(root, text=f"Welcome, {logged_in_user}", **label_style).pack(pady=20)
        tk.Button(root, text="Add Complaint", **button_style, command=add_complaint).pack(pady=10)
        tk.Button(root, text="View Complaints", **button_style, command=view_complaints).pack(pady=10)
        tk.Button(root, text="Withdraw Complaint", **button_style, command=withdraw_complaint).pack(pady=10)
        tk.Button(root, text="Logout", **button_style, command=logout).pack(pady=20)
    else:
        tk.Label(root, text="Welcome to Complaint Management System", font=("Helvetica", 18), bg='#f0f0f0').pack(pady=20)
        tk.Button(root, text="Login", **button_style, command=login).pack(pady=10)
        tk.Button(root, text="Signup", **button_style, command=signup).pack(pady=10)

# Start the application
main_interface()
root.mainloop()
