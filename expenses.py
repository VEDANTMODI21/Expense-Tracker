import os
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error
from tkcalendar import DateEntry
from datetime import datetime
import csv

# Connect to the database
try:
    db_conn = mysql.connector.connect(
        host="localhost",
        user="user",  # Your MySQL username
        password="yourpassword",  # Your MySQL password
        database="expense"  # Your MySQL database name
    )
    if db_conn.is_connected():
        print("Connection successful to the database!")
except Error as e:
    print(f"Error: {e}")
    db_conn = None

db_cursor = db_conn.cursor()

# Create expenses table if it doesn't exist
db_cursor.execute("""CREATE TABLE IF NOT EXISTS expenses (
        id INT AUTO_INCREMENT PRIMARY KEY,
        date DATE,  -- Changed to DATE type
        category VARCHAR(50),
        amount FLOAT
    )""")

# Create expense_reports table if it doesn't exist
db_cursor.execute("""CREATE TABLE IF NOT EXISTS expense_reports (
        id INT AUTO_INCREMENT PRIMARY KEY,
        category VARCHAR(50),
        total_amount FLOAT,
        report_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

db_conn.commit()

# Functions

def add_expense():
    date = date_entry.get_date()  # Get date from DateEntry
    category = category_entry.get()
    amount = amount_entry.get()

    if category and amount:
        try:
            amount_float = float(amount)  # Convert amount to float
            db_cursor.execute("INSERT INTO expenses (date, category, amount) VALUES (%s, %s, %s)",
                              (date, category, amount_float))  # Date is already in correct format
            db_conn.commit()
            status_label.config(text="Expense added successfully!", foreground="green")
            category_entry.delete(0, tk.END)
            amount_entry.delete(0, tk.END)
            view_expenses()  # Refresh the expense view
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to add expense: {e}")
    else:
        status_label.config(text="Please fill all the fields!", foreground="red")


def delete_expense():
    selected_item = expenses_tree.selection()
    if selected_item:
        item_text = expenses_tree.item(selected_item, "values")
        date, category, amount = item_text
        try:
            db_cursor.execute("DELETE FROM expenses WHERE date = %s AND category = %s AND amount = %s",
                              (date, category, float(amount)))
            db_conn.commit()
            status_label.config(text="Expense deleted successfully!", foreground="green")
            view_expenses()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to delete expense: {e}")
    else:
        status_label.config(text="Please select an expense to delete!", foreground="red")


def view_expenses():
    try:
        db_cursor.execute("SELECT date, category, amount FROM expenses ORDER BY date ASC")
        rows = db_cursor.fetchall()

        total_expense = sum(row[2] for row in rows)

        expenses_tree.delete(*expenses_tree.get_children())

        for row in rows:
            expenses_tree.insert("", tk.END, values=(row[0], row[1], row[2]))

        total_label.config(text=f"Total Expense: {total_expense:.2f}")
    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to retrieve expenses: {e}")


def generate_report():
    try:
        db_cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
        rows = db_cursor.fetchall()
        report_tree.delete(*report_tree.get_children())

        for row in rows:
            report_tree.insert("", tk.END, values=row)

        total_report_expense = sum(row[1] for row in rows)
        total_report_label.config(text=f"Total Expenses: {total_report_expense:.2f}")
    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to generate report: {e}")


def download_report_as_csv(report_type):
    try:
        if report_type == "monthly":
            month = month_entry.get()
            year = year_entry.get()
            like_pattern = f"{year}-{month}-%"

            # Modify the query to get each expense with its date, category, and amount
            db_cursor.execute("SELECT date, category, amount FROM expenses WHERE date LIKE %s ORDER BY date ASC",
                              (like_pattern,))
            rows = db_cursor.fetchall()

            # Save each record with date, category, and amount to CSV
            with open(f"monthly_report_{year}_{month}.csv", mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Category", "Amount"])  # Add "Date" to the CSV header
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Monthly report saved as monthly_report_{year}_{month}.csv")

        elif report_type == "yearly":
            year = year_entry_yearly.get()
            db_cursor.execute("SELECT date, category, amount FROM expenses WHERE YEAR(date) = %s ORDER BY date ASC",
                              (year,))
            rows = db_cursor.fetchall()

            # Save each record with date, category, and amount to CSV
            with open(f"yearly_report_{year}.csv", mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Category", "Amount"])  # Add "Date" to the CSV header
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Yearly report saved as yearly_report_{year}.csv")
    except Exception as e:
        messagebox.showerror("File Error", f"Failed to save report: {e}")


def generate_monthly_report():
    month = month_entry.get()
    year = year_entry.get()

    # Input validation for month and year
    if len(month) != 2 or not month.isdigit() or not (1 <= int(month) <= 12):
        messagebox.showerror("Input Error", "Please enter a valid month (MM).")
        return

    if len(year) != 4 or not year.isdigit():
        messagebox.showerror("Input Error", "Please enter a valid year (YYYY).")
        return

    try:
        # Pattern to match the selected month in the database
        like_pattern = f"{year}-{month}-%"
        db_cursor.execute("SELECT date, category, amount FROM expenses WHERE date LIKE %s ORDER BY date ASC",
                          (like_pattern,))
        rows = db_cursor.fetchall()

        if not rows:
            messagebox.showinfo("No Data", "No transactions found for this month.")
            return

        # Clear the Treeview before inserting new data
        monthly_report_tree.delete(*monthly_report_tree.get_children())

        # Insert all rows (date, category, expense) into the Treeview
        for row in rows:
            monthly_report_tree.insert("", tk.END, values=row)

        # Calculate the total monthly expense and display it
        total_monthly_expense = sum(row[2] for row in rows)
        total_monthly_label.config(text=f"Total Expenses for {month}/{year}: {total_monthly_expense:.2f}")

    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to generate monthly report: {e}")


def generate_yearly_report():
    year = year_entry_yearly.get()

    if len(year) != 4 or not year.isdigit():
        messagebox.showerror("Input Error", "Please enter a valid year (YYYY).")
        return

    try:
        db_cursor.execute("SELECT date, category, amount FROM expenses WHERE YEAR(date) = %s ORDER BY date ASC", (year,))
        rows = db_cursor.fetchall()

        if not rows:
            messagebox.showinfo("No Data", "No expenses found for this year.")
            return

        # Clear the treeview before inserting new data
        yearly_report_tree.delete(*yearly_report_tree.get_children())

        for row in rows:
            yearly_report_tree.insert("", tk.END, values=row)

        total_yearly_expense = sum(row[2] for row in rows)
        total_yearly_label.config(text=f"Total Expenses for {year}: {total_yearly_expense:.2f}")

    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to generate yearly report: {e}")


# Create the main application window
root = tk.Tk()
root.title("Expense Tracker")
root.geometry("800x600")
root.configure(bg="#f0f8ff")

# Create a style
style = ttk.Style()
style.configure("TNotebook", tabposition='n', background="#e6f7ff")
style.configure("TNotebook.Tab", background="#e6f7ff", padding=[10, 5])
style.configure("TFrame", background="#e6f7ff")
style.configure("TLabel", background="#e6f7ff", font=('Arial', 12))
style.configure("TButton", font=('Arial', 12), padding=5)

# Create a notebook (tabbed interface)
notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

# Create frames for each page
add_expense_frame = ttk.Frame(notebook)
view_expenses_frame = ttk.Frame(notebook)
report_frame = ttk.Frame(notebook)
monthly_report_frame = ttk.Frame(notebook)
yearly_report_frame = ttk.Frame(notebook)

notebook.add(add_expense_frame, text="Add Expense")
notebook.add(view_expenses_frame, text="View Expenses")
notebook.add(report_frame, text="Generate Reports")
notebook.add(monthly_report_frame, text="Monthly Report")
notebook.add(yearly_report_frame, text="Yearly Report")

# Frame for adding expense
ttk.Label(add_expense_frame, text="Date:").grid(row=0, column=0, padx=10, pady=10)
date_entry = DateEntry(add_expense_frame, date_pattern='yyyy-mm-dd')
date_entry.grid(row=0, column=1, padx=10, pady=10)

ttk.Label(add_expense_frame, text="Category:").grid(row=1, column=0, padx=10, pady=10)
category_entry = ttk.Entry(add_expense_frame)
category_entry.grid(row=1, column=1, padx=10, pady=10)

ttk.Label(add_expense_frame, text="Amount:").grid(row=2, column=0, padx=10, pady=10)
amount_entry = ttk.Entry(add_expense_frame)
amount_entry.grid(row=2, column=1, padx=10, pady=10)

ttk.Button(add_expense_frame, text="Add Expense", command=add_expense).grid(row=3, column=0, columnspan=2, pady=20)
status_label = ttk.Label(add_expense_frame, text="", foreground="green")
status_label.grid(row=4, column=0, columnspan=2)

# Frame for viewing expenses
columns = ("date", "category", "amount")
expenses_tree = ttk.Treeview(view_expenses_frame, columns=columns, show="headings")
expenses_tree.heading("date", text="Date")
expenses_tree.heading("category", text="Category")
expenses_tree.heading("amount", text="Amount")

expenses_tree.pack(padx=10, pady=10, fill='both', expand=True)
ttk.Button(view_expenses_frame, text="Delete Expense", command=delete_expense).pack(pady=10)

total_label = ttk.Label(view_expenses_frame, text="Total Expense: 0.00")
total_label.pack(pady=10)

# Frame for generating reports
ttk.Button(report_frame, text="Generate Report", command=generate_report).grid(row=0, column=0, padx=10, pady=10)
report_tree = ttk.Treeview(report_frame, columns=("category", "total_amount"), show="headings")
report_tree.heading("category", text="Category")
report_tree.heading("total_amount", text="Total Amount")
report_tree.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')

total_report_label = ttk.Label(report_frame, text="Total Expenses: 0.00")
total_report_label.grid(row=2, column=0, padx=10, pady=10)

# Frame for generating monthly report
ttk.Label(monthly_report_frame, text="Month (MM):").grid(row=0, column=0, padx=10, pady=10)
month_entry = ttk.Entry(monthly_report_frame)
month_entry.grid(row=0, column=1, padx=10, pady=10)

ttk.Label(monthly_report_frame, text="Year (YYYY):").grid(row=1, column=0, padx=10, pady=10)
year_entry = ttk.Entry(monthly_report_frame)
year_entry.grid(row=1, column=1, padx=10, pady=10)

ttk.Button(monthly_report_frame, text="Generate Monthly Report", command=generate_monthly_report).grid(row=2, column=0, columnspan=2, pady=10)

monthly_report_tree = ttk.Treeview(monthly_report_frame, columns=("date", "category", "amount"), show="headings")
monthly_report_tree.heading("date", text="Date")
monthly_report_tree.heading("category", text="Category")
monthly_report_tree.heading("amount", text="Amount")
monthly_report_tree.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')

total_monthly_label = ttk.Label(monthly_report_frame, text="Total Expenses for Month/Year: 0.00")
total_monthly_label.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

ttk.Button(monthly_report_frame, text="Download as CSV", command=lambda: download_report_as_csv("monthly")).grid(row=5, column=0, columnspan=2, pady=10)

# Frame for generating yearly report
ttk.Label(yearly_report_frame, text="Year (YYYY):").grid(row=0, column=0, padx=10, pady=10)
year_entry_yearly = ttk.Entry(yearly_report_frame)
year_entry_yearly.grid(row=0, column=1, padx=10, pady=10)

ttk.Button(yearly_report_frame, text="Generate Yearly Report", command=generate_yearly_report).grid(row=1, column=0, columnspan=2, pady=10)

yearly_report_tree = ttk.Treeview(yearly_report_frame, columns=("date", "category", "amount"), show="headings")
yearly_report_tree.heading("date", text="Date")
yearly_report_tree.heading("category", text="Category")
yearly_report_tree.heading("amount", text="Amount")
yearly_report_tree.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')

total_yearly_label = ttk.Label(yearly_report_frame, text="Total Expenses for Year: 0.00")
total_yearly_label.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

ttk.Button(yearly_report_frame, text="Download as CSV", command=lambda: download_report_as_csv("yearly")).grid(row=4, column=0, columnspan=2, pady=10)

root.mainloop()
