import csv
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
from tkinter import Button, Entry, Text, font, messagebox, Toplevel, Scrollbar, Frame, Checkbutton, IntVar, Label
from barcode import Code128
from barcode.writer import ImageWriter
import subprocess
from tkinter import font as tkfont  # Importing the font module for custom fonts
import tkinter as tk
from tkinter import ttk  # For themed widgets
from datetime import datetime, timedelta
from threading import Thread
from dropbox_backup import backup_files
import sys

# Load the customer data from the CSV file
customer_data = pd.read_csv(r"C:\notifynpick_final\customer.csv")

# Email configuration
sender_email = 'villagemail6@gmail.com'
sender_password = 'sqps ssqy rikp wlfd'

# Path for the log file
log_file_path = 'history_log.csv'

mailbox_number = ""
customer_name = None
customer_email = None
decoded_tracking_id = None
parcels=""

# Function to log history with "Check Out Time" column
def log_history(Mailbox_Number, customer_name, customer_email, tracking_number, carrier, unique_barcode, check_out_time=None):
    
    if not os.path.exists(log_file_path):
        #df = pd.read_csv(log_file_path, dtype={'Tracking ID': str})
        with open(log_file_path, 'w') as f:
            f.write("Mailbox Number,Customer Name,Customer Email,Tracking ID,Carrier,Unique Barcode,Check-in Time,Check-out Time\n")
    with open(log_file_path, 'a') as f:
        check_in_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        check_out_time = check_out_time if check_out_time else "null"
        carrier = carrier if carrier else "null"
        tracking_number = tracking_number if tracking_number else "null"
        f.write(f"{Mailbox_Number},{customer_name},{customer_email},{tracking_number},{carrier},{unique_barcode},{check_in_time},{check_out_time}\n")
def log_check_out(selected_rows):
    if os.path.exists(log_file_path):
        df = pd.read_csv(log_file_path)
        check_out_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for index in selected_rows:
            df.at[index, 'Check-out Time'] = check_out_time
        df.to_csv(log_file_path, index=False)

def check_out_email(mailbox_number, parcels):
    global customer_name, customer_email
    if not customer_email:
        #messagebox.showerror("Error", "Invalid email address. Cannot send email.")
        return
    
    subject = "Parcel Check-Out Confirmation from Village Mail & More"
    body = f"""Dear {customer_name},

The following parcels associated with your mailbox number [{mailbox_number}] have been checked out:

"""
    # Add details for each parcel
    for parcel in parcels:
        tracking_id = parcel.get('tracking_id', 'N/A')
        carrier = parcel.get('carrier', 'N/A')
        unique_barcode = parcel.get('unique_barcode', 'N/A')
        check_out_time = parcel.get('check_out_time', 'N/A')
        body += f"""
        Tracking ID: {tracking_id}
        Barcode: {unique_barcode}
        Carrier: {carrier}
        Check-out Time: {check_out_time}
        """

    body += """
Please reach out if you have any questions or require further assistance.

Thank you for choosing Village Mail & More!

Best regards,
Village Mail & More
"""

    # Setting up the email
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = customer_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Attempt to send email
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, customer_email, msg.as_string())
        
        #print("Check-out email sent successfully to:", customer_email)
        #messagebox.showinfo("Success", "Check-out email sent successfully.")
    except Exception as e:
        #print("Failed to send check-out email. Error:", str(e))
        messagebox.showerror("Error", f"Failed to send check-out email: {e}")
    

def check_out():
    mailbox_label.pack(pady=5)
    mailbox_entry.pack(pady=5)

    pmb = mailbox_entry.get().strip()

    if not pmb:
        # Messagebox if PMB is not entered
        #messagebox.showerror("Error", "Please enter the PMB number for checkout.")
        return

    if os.path.exists(log_file_path):
        df = pd.read_csv(log_file_path)

        # Filter out parcels that are already checked out
        filtered_df = df[(df['Mailbox Number'] == int(pmb)) & ((df['Check-out Time'] == "null") | pd.isna(df['Check-out Time']))]

        if filtered_df.empty:
            # If no parcels for checkout, show an error message
            messagebox.showinfo("Check-out", f"No parcels found for PMB {pmb} that require checkout.")
            mailbox_entry.delete(0, tk.END)  # Clear the entry field
            mailbox_label.pack_forget()  # Remove the mailbox label
            mailbox_entry.pack_forget()  # Remove the mailbox entry field
            return
        
        check_out_window = Toplevel(window)
        check_out_window.title(f"Check-out for PMB {pmb}")

        # Scrollable frame
        frame = Frame(check_out_window)
        frame.pack(fill=tk.BOTH, expand=True)

        selected_rows = []
        checkbox_vars = []

        # Display parcels with checkboxes
        for idx, row in filtered_df.iterrows():
            var = IntVar()
            checkbox_vars.append((var, row))
            checkbutton = Checkbutton(frame, text=f"Tracking ID: {row['Tracking ID']}, Carrier: {row['Carrier']}, Check-in Time: {row['Check-in Time']}", variable=var)
            checkbutton.pack(anchor='w')

        def update_check_out():
            global parcels
            parcels = []
            selected_rows = []  # Reset the selected rows

            for var, row in checkbox_vars:
                if var.get() == 1:
                    selected_rows.append(row)  # Add row to selected_rows
                    parcels.append({
                        "tracking_id": row['Tracking ID'],
                        "unique_barcode": row['Unique Barcode'],
                        "carrier": row['Carrier'],
                        "check_out_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })

            log_check_out([row.name for row in selected_rows])  # Log the checkout

            # After confirming checkout, hide or disable mailbox input
            mailbox_label.pack_forget()  # Remove the label
            mailbox_entry.pack_forget()  # Remove the entry field

            # Optionally, you can clear the field to prevent reuse
            mailbox_entry.delete(0, tk.END)

        def get_email_by_mailbox(mailbox_number):
            try:
                mailbox_number = str(mailbox_number).strip()
                customer_data["Mailbox Number"] = customer_data["Mailbox Number"].astype(str).str.strip()

                customer_row = customer_data[customer_data["Mailbox Number"] == mailbox_number]

                if not customer_row.empty:
                    email = customer_row['Email ID'].values[0]
                    name = customer_row['Customer Name'].values[0]
                    return name, email
                else:
                    return None, None
            except Exception as e:
                return None, None

        def handle_send_followup():
            global customer_name, customer_email
            customer_name, customer_email = get_email_by_mailbox(pmb)
            if customer_email:
                check_out_email(pmb, parcels)
                check_out_window.destroy()
            else:
                messagebox.showerror("Error", "No customer found for the entered PMB.")

        confirm_button = tk.Button(check_out_window, text="Confirm Check-out", command=update_check_out)
        confirm_button.pack(pady=10)

        send_followup_button = tk.Button(check_out_window, text="Follow-up Email", command=handle_send_followup)
        send_followup_button.pack(pady=10)
        
    

    # Create the canvas widget
    canvas = tk.Canvas(frame)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Create the scrollbar widget and associate it with the canvas
    Scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    Scrollbar.pack(side=tk.RIGHT, fill="y")

    # Configure the canvas to update the scrollbar
    canvas.config(yscrollcommand=Scrollbar.set)
    # In your check-out window creation logic
    canvas = create_canvas_with_scroll(frame)
   

def create_canvas_with_scroll(frame):
    # Create the canvas widget
    canvas = tk.Canvas(frame)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Create the scrollbar widget and associate it with the canvas
    scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill="y")

    # Configure the canvas to update the scrollbar
    canvas.config(yscrollcommand=scrollbar.set)

    # Check if canvas is still part of the window before binding mouse wheel event
    def bind_mousewheel(event, canvas=canvas):
        if canvas.winfo_exists():  # Check if the canvas widget still exists
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", bind_mousewheel)  # Bind the mouse wheel event

    return canvas



# Check-in functionality: Opens the original FINALCHECKIN.py script
def check_in():
   
    # Resolve the path to finalcheckin.py in the bundled executable
    script_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    finalcheckin_path = os.path.join(script_dir, "finalcheckin.py")

    # Call the subprocess
    subprocess.run(["python", finalcheckin_path])

# Management functionality to display history log in a new window
def management():
    if os.path.exists(log_file_path):
        log_df = pd.read_csv(log_file_path)

        # Create a new window for displaying the history log
        history_window = Toplevel(window)
        history_window.title("History Log")
        history_window.geometry("900x600")

        # Scrollable frame
        frame = Frame(history_window)
        frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create canvas for scrolling
        canvas = tk.Canvas(frame, yscrollcommand=scrollbar.set)
        scrollbar.config(command=canvas.yview)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Frame inside the canvas to hold log data
        log_frame = Frame(canvas)
        canvas.create_window((0, 0), window=log_frame, anchor="nw")

        # Display log data as labels in grid format
        def display_data(dataframe):
            """Clears the frame and displays the dataframe."""
            for widget in log_frame.winfo_children():
                widget.destroy()

            # Add headers
            for i, column in enumerate(dataframe.columns):
                Label(log_frame, text=column, borderwidth=2, relief="groove").grid(row=0, column=i, sticky="nsew")

            # Add data rows
            for row_idx, row in dataframe.iterrows():
                for col_idx, value in enumerate(row):
                    Label(log_frame, text=value, borderwidth=1, relief="groove").grid(row=row_idx+1, column=col_idx, sticky="nsew")

            # Update scroll region
            log_frame.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))

        # Initially display the full log data
        display_data(log_df)

        # Search Section
        search_frame = Frame(history_window)
        search_frame.pack(fill=tk.X, pady=10)

        search_label = Label(search_frame, text="Search PMB Number:")
        search_label.pack(side=tk.LEFT, padx=5)

        search_entry = Entry(search_frame)
        search_entry.pack(side=tk.LEFT, padx=5)

        def search_pmb():
            """Filters and displays data for a specific PMB number."""
            pmb_number = search_entry.get().strip()
            if not pmb_number:
                messagebox.showerror("Error", "Please enter a PMB number.")
                return

            try:
                filtered_df = log_df[log_df['Mailbox Number'] == int(pmb_number)]
                if filtered_df.empty:
                    messagebox.showinfo("Search Result", f"No records found for PMB {pmb_number}.")
                else:
                    display_data(filtered_df)
            except ValueError:
                messagebox.showerror("Error", "Invalid PMB number format.")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")

        search_button = Button(search_frame, text="Search", command=search_pmb)
        search_button.pack(side=tk.LEFT, padx=5)

    else:
        messagebox.showerror("Error", "History log file does not exist.")


def display_log(result_text):
    """Displays the entire log file."""
    try:
        log_df = pd.read_csv(log_file_path)
        result_text.delete("1.0", tk.END)
        result_text.insert(tk.END, "Entire Log File:\n\n")
        result_text.insert(tk.END, log_df.to_string(index=False))
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load log file: {e}")

def view_customer_details():
    customer_file_path = 'customer.csv'  # Path to your customer.csv file

    if os.path.exists(customer_file_path):
        customer_df = pd.read_csv(customer_file_path)  # Load customer data
        customer_window = Toplevel(window)
        customer_window.title("Customer Details")

        # Set window size dynamically based on data
        max_width = 800  # Limit maximum width
        max_height = 600  # Limit maximum height
        row_count, column_count = customer_df.shape
        table_width = min(max_width, column_count * 150)
        table_height = min(max_height, (row_count + 1) * 30)
        customer_window.geometry(f"{table_width}x{table_height}")

        # Create a frame to hold the table and scrollbars
        frame = Frame(customer_window)
        frame.pack(fill=tk.BOTH, expand=True)

        # Add scrollbars
        v_scrollbar = Scrollbar(frame, orient="vertical")
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar = Scrollbar(frame, orient="horizontal")
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Add canvas for the table
        canvas = tk.Canvas(frame, yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        v_scrollbar.config(command=canvas.yview)
        h_scrollbar.config(command=canvas.xview)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Frame inside canvas for table data
        table_frame = Frame(canvas)
        canvas.create_window((0, 0), window=table_frame, anchor="nw")

        # Add table header
        for col_idx, column in enumerate(customer_df.columns):
            tk.Label(table_frame, text=column, borderwidth=2, relief="groove", bg="lightgray").grid(row=0, column=col_idx, sticky="nsew")

        # Add table rows
        for row_idx, row in customer_df.iloc[::-1].iterrows():  # Reversed order
            for col_idx, value in enumerate(row):
                tk.Label(table_frame, text=value, borderwidth=1, relief="groove").grid(row=row_idx + 1, column=col_idx, sticky="nsew")

        # Update scroll region
        table_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

    else:
        messagebox.showerror("Error", "Customer file does not exist.")


# Function to open the Customer Management window
def open_customer_management():
    management_window = Toplevel(window)
    management_window.title("Customer Management")
    management_window.geometry("400x300")

    # New Customer Button
    def add_new_customer():
        new_customer_window = Toplevel(management_window)
        new_customer_window.title("Add New Customer")
        new_customer_window.geometry("400x400")

    # Entry fields for customer details
        labels = ["Customer Name", "Email ID", "Phone Number", "Mailbox Number", "Address"]
        entries = {}
        for label in labels:
            lbl = tk.Label(new_customer_window, text=label)
            lbl.pack(pady=5)
            entry = tk.Entry(new_customer_window)
            entry.pack(pady=5)
            entries[label] = entry

    # Function to save new customer
        def save_new_customer(entries, new_customer_window):
        # Retrieve input values
            customer_data = {label: entry.get().strip() for label, entry in entries.items()}

        # Check if all fields are filled
            if any(value == "" for value in customer_data.values()):
                messagebox.showerror("Error", "All fields are required!")
                return

            mailbox_number = customer_data["Mailbox Number"]

        # Load the existing customer data
            try:
                customer_data_df = pd.read_csv('customer.csv', dtype={'Mailbox Number': str})
            except FileNotFoundError:
            # If the file doesn't exist, create an empty DataFrame
                customer_data_df = pd.DataFrame(columns=["Customer Name", "Email ID", "Phone Number", "Mailbox Number", "Address"])

        # Check if the mailbox number already exists
            if mailbox_number in customer_data_df["Mailbox Number"].values:
                messagebox.showerror("Error", "Mailbox number already exists!")
                return

        # Append the new customer to the file
            try:
                with open('customer.csv', mode='a', newline='', encoding='utf-8') as file:
                    writer = csv.DictWriter(file, fieldnames=["Customer Name", "Mailbox Number", "Phone Number", "Email ID", "Address"])
                    if file.tell() == 0:  # Write the header only if the file is empty
                        writer.writeheader()
                    writer.writerow({
                        "Customer Name": customer_data["Customer Name"],
                        "Email ID": customer_data["Email ID"],
                        "Phone Number": customer_data["Phone Number"],
                        "Mailbox Number": customer_data["Mailbox Number"],
                        "Address": customer_data["Address"]
                    })
                messagebox.showinfo("Success", "Customer added successfully!")
                new_customer_window.destroy()  # Close the window after saving
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save new customer: {e}")

    # Save button to trigger the save function (placed at the end)
        save_button = tk.Button(new_customer_window, text="Save", command=lambda: save_new_customer(entries, new_customer_window))
        save_button.pack(pady=20)  # Added padding for better UI placement



    # Update Customer Button
    def update_customer():
        update_window = Toplevel(management_window)
        update_window.title("Update Customer")
        update_window.geometry("400x400")

        lbl = tk.Label(update_window, text="Enter Mailbox Number to Update:")
        lbl.pack(pady=5)
        mailbox_entry = tk.Entry(update_window)
        mailbox_entry.pack(pady=5)

        def load_customer_details():
            mailbox_number = mailbox_entry.get().strip()

        # Load customer data
            try:
                customer_data_df = pd.read_csv('customer.csv', dtype={'Mailbox Number': str})
            except FileNotFoundError:
                messagebox.showerror("Error", "The customer file does not exist.")
                return

            if mailbox_number not in customer_data_df["Mailbox Number"].values:
                messagebox.showerror("Error", "Mailbox number not found!")
                return

            customer_row = customer_data_df[customer_data_df["Mailbox Number"] == mailbox_number]

        # Display fields for updating
            fields = ["Customer Name", "Email ID", "Phone Number", "Address"]
            entries = {}
            for field in fields:
                lbl = tk.Label(update_window, text=f"Update {field}:")
                lbl.pack(pady=5)
                entry = tk.Entry(update_window)
                entry.insert(0, customer_row[field].values[0])
                entry.pack(pady=5)
                entries[field] = entry

            def save_updates():
                for field, entry in entries.items():
                    customer_data_df.loc[customer_data_df["Mailbox Number"] == mailbox_number, field] = entry.get().strip()
                customer_data_df.to_csv('customer.csv', index=False)
                messagebox.showinfo("Success", "Customer details updated!")
                update_window.destroy()

            save_button = tk.Button(update_window, text="Save Updates", command=save_updates)
            save_button.pack(pady=20)

        load_button = tk.Button(update_window, text="Load Customer", command=load_customer_details)
        load_button.pack(pady=10)

    # Delete Customer Button
    def confirm_delete():
        delete_window = Toplevel(management_window)
        delete_window.title("Delete Customer")
        delete_window.geometry("400x200")

        lbl = tk.Label(delete_window, text="Enter Mailbox Number to Delete:")
        lbl.pack(pady=5)
        mailbox_entry = tk.Entry(delete_window)
        mailbox_entry.pack(pady=5)

        def delete_customer():
            mailbox_number = mailbox_entry.get().strip()

        # Load customer data
            try:
                customer_data = pd.read_csv('customer.csv', dtype={'Mailbox Number': str})
            except FileNotFoundError:
                messagebox.showerror("Error", "The customer file does not exist.")
                return

            if mailbox_number not in customer_data["Mailbox Number"].values:
                messagebox.showerror("Error", "Mailbox number not found!")
                return

        # Remove the customer
            customer_data = customer_data[customer_data["Mailbox Number"] != mailbox_number]
            customer_data.to_csv('customer.csv', index=False)
            messagebox.showinfo("Success", "Customer deleted successfully!")
            delete_window.destroy()

        delete_button = tk.Button(delete_window, text="Delete", command=delete_customer)
        delete_button.pack(pady=10)
        tk.Button(management_window, text="Delete Customer", command=delete_customer).pack(pady=10)

    # Add Buttons to Management Window
    tk.Button(management_window, text="New Customer", command=add_new_customer).pack(pady=10)
    tk.Button(management_window, text="Update Customer", command=update_customer).pack(pady=10)
    tk.Button(management_window, text="Delete Customer", command=confirm_delete).pack(pady=10)
    
help_window = None

def show_help():
    global help_window  # Use the global help_window variable

    # Check if the help window is already open
    if help_window is None or not help_window.winfo_exists():
        # Create a new Help window if not already created
        help_window = Toplevel(window)
        help_window.title("User manual")
        help_window.geometry("1000x500")  # Adjust the size as necessary

        # Create a scrollable frame for the content
        canvas = tk.Canvas(help_window)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create vertical scrollbar and bind it to the canvas
        scrollbar_v = tk.Scrollbar(help_window, orient="vertical", command=canvas.yview)
        scrollbar_v.pack(side=tk.RIGHT, fill="y")
        canvas.config(yscrollcommand=scrollbar_v.set)

        # Bind mouse wheel event to canvas for touchpad scrolling
        canvas.bind_all("<MouseWheel>", lambda event, canvas=canvas: canvas.yview_scroll(int(-1*(event.delta/120)), "units"))

        # Create a frame inside the canvas to hold the content
        help_frame = tk.Frame(canvas, padx=20, pady=20)
        canvas.create_window((0, 0), window=help_frame, anchor="nw")

        # Default fonts for headings and text (back to previous font)
        section_heading_font = ("Helvetica", 20, "bold")
        text_font = ("Arial", 12)

        # User Manual Text
        user_manual_text = """
        User Manual for Village Mail & More
        -----------------------------------------------------

        🎉 Welcome to Village Mail & More! 
        Your efficient and user-friendly solution for parcel management. This manual provides a detailed guide to help you master the system’s features, 
        including Check-In, Check-Out, Customer Management, and the new Backup Manager! 📦✨

        Step 1: New Customer 🆕
        ------------------------
        To register a new customer:

        1. Enter the following details:
           👤 Customer Name: Full name of the customer.
           📧 Email ID: Customer’s email address.
           📞 Phone Number: A valid contact number.
           📬 Mailbox Number: A unique number assigned to the customer (must be unique).
           🏠 Address: Customer’s physical address.
        2. Click 💾 Save to store the details.
        3. The system now links this customer to their assigned mailbox, allowing them to receive parcels.

        Step 2: Update Customer ✏️
        ---------------------------
        To update an existing customer’s details:

        1. Enter the Mailbox Number of the customer.
        2. Retrieve and modify their information:
           👤 Name
           📧 Email
           📞 Phone Number
           🏠 Address
        3. Click 💾 Save Updates to apply the changes.

        Step 3: Delete Customer ❌
        --------------------------
        To remove a customer:

        1. Enter the Mailbox Number of the customer.
        2. Confirm the action by clicking Delete.
        3. This will permanently remove the customer and their records from the system.

        Step 4: Check-In (Parcel Registration) 📥
        -----------------------------------------
        To register a new parcel:

        1. Enter the Mailbox Number of the recipient.
        2. Add parcel details:
           🔍 Tracking ID: The unique tracking number.
           🚚 Carrier: Shipping provider (e.g., FedEx, UPS).
           🔑 Unique Barcode: Auto-generated for parcel identification.
           ⏰ Check-In Time: Timestamp for registration.
        3. Click Confirm Check-In to save the details.
        4. The customer will receive a notification about their parcel.

        Step 5: Check-Out (Parcel Collection) 📤
        -----------------------------------------
        To allow customers to collect parcels:

        1. Enter the Mailbox Number of the recipient.
        2. View all pending parcels and select the ones for pickup.
        3. Click ✅Confirm Check-Out to update the system.
        4. A Follow-Up Email will be sent to the customer with details like:
           🔍 Tracking ID
           🚚 Carrier
           ⏰ Check-Out Time

        Step 6: Backup Manager 🔒💾 (New Feature)
        ----------------------------------------
        Ensure data safety by creating backups of all system records:

        1. Navigate to the Backup Manager section in the menu.
        2. Click 📂 Backup Now to generate a backup of all .csv files, including:
           🗂️Customer records
           📦 Parcel logs
        3. Save the backup securely on an external drive or cloud storage.
        💡 Tip: Regular backups protect against data loss or corruption.

        Additional Features
        -------------------
        Management 🖥️
        - View the history of Check-Ins and Check-Outs.
        - Use the search bar to locate parcels by Mailbox Number quickly.

        Customer Management 🤝
        - Add, update, or delete customer records.
        - Ensure all information is accurate before saving changes.

        System Workflow 🔄
        -------------------
        Customer Records:
        - Each customer is assigned a unique Mailbox Number that links them to their parcels.

        Parcel Tracking:
        - Parcels are tracked using their Tracking ID and associated mailbox, ensuring secure handling.

        Notifications:
        - Customers receive timely email updates on parcel status, reducing the need for inquiries.

        Backup and Recovery:
        - The Backup Manager ensures your data remains safe and recoverable at all times.

        Key Benefits 🌟
        ----------------
        🎯 Accurate Parcel Management: Unique identifiers prevent errors.
        ⚡ Streamlined Customer Service: Quick updates and deletions maintain efficiency.
        🔒 Effortless Backup: Safeguard your data with ease.
        📧 Automated Notifications: Keep customers informed at all times.

        By following this guide, Village Mail & More ensures a smooth and professional experience for all users! 🌟

        """

        # Display the user manual text
        tk.Label(help_frame, text=user_manual_text, justify="left", anchor="w").pack(pady=5)

        # Update the scroll region
        help_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

# Create the Help label only once at the beginning
    if 'help_label' not in globals():  # Check if the Help label exists
        help_label = tk.Label(window, text="Help", fg="yellow", cursor="hand2")
        help_label.pack(side="bottom", anchor="se", padx=10, pady=10)  # Placed at the bottom-right corner
        help_label.bind("<Button-1>", lambda e: show_help())  # Bind click event to show_help function



# Initialize the main window
window = tk.Tk()
window.title("Village Mail & More")
window.geometry("800x600")
window.configure(bg='#E6F0FF')  # Light blue background

# Define fonts
title_font = font.Font(family="Arial", size=24, weight="bold")
button_font = font.Font(family="Arial", size=12)

# Title Section
title_label = tk.Label(window, text="Village Mail & More", bg='#E6F0FF', fg="steelblue", font=title_font)
title_label.pack(pady=20)

# Frame for Buttons
button_frame = tk.Frame(window, bg='#E6F0FF')
button_frame.pack(pady=50)

# Define button colors and hover effects in shades of blue
button_color = '#76b7f6'  # Default button color (blue)
button_hover_color = '#5fa8f0'  # Hover button color (darker blue)

# Function to change button color on hover
def on_enter(button):
    button['background'] = button_hover_color

def on_leave(button):
    button['background'] = button_color

def backup_options():
    backup_window = tk.Toplevel(window)
    backup_window.title("Backup Options")
    backup_window.geometry("300x200")
    tk.Label(backup_window, text="Choose Backup Frequency").pack(pady=10)
    tk.Button(backup_window, text="Backup Now", command=backup_files, bg=button_color, activebackground=button_hover_color).pack(pady=10)

# Create Buttons with the original field names and reduced size
check_in_button = tk.Button(button_frame, text="Check-in", font=button_font, width=20, height=2, relief="raised", 
                             bg=button_color, activebackground=button_hover_color, command=check_in)
check_in_button.grid(row=0, column=0, padx=20, pady=10)
check_in_button.bind("<Enter>", lambda event: on_enter(check_in_button))
check_in_button.bind("<Leave>", lambda event: on_leave(check_in_button))

check_out_button = tk.Button(button_frame, text="Check-out", font=button_font, width=20, height=2, relief="raised", 
                              bg=button_color, activebackground=button_hover_color, command=check_out)
check_out_button.grid(row=0, column=1, padx=20, pady=10)
check_out_button.bind("<Enter>", lambda event: on_enter(check_out_button))
check_out_button.bind("<Leave>", lambda event: on_leave(check_out_button))

management_button = tk.Button(button_frame, text="Package Management", font=button_font, width=20, height=2, relief="raised", 
                              bg=button_color, activebackground=button_hover_color, command=management)
management_button.grid(row=0, column=2, padx=20, pady=10)
management_button.bind("<Enter>", lambda event: on_enter(management_button))
management_button.bind("<Leave>", lambda event: on_leave(management_button))

view_customer_button = tk.Button(button_frame, text="Contacts", font=button_font, width=20, height=2, relief="raised", 
                                  bg=button_color, activebackground=button_hover_color, command=view_customer_details)
view_customer_button.grid(row=1, column=0, padx=20, pady=10)
view_customer_button.bind("<Enter>", lambda event: on_enter(view_customer_button))
view_customer_button.bind("<Leave>", lambda event: on_leave(view_customer_button))

customer_management_button = tk.Button(button_frame, text="Contacts Settings", font=button_font, width=20, height=2, relief="raised", 
                                       bg=button_color, activebackground=button_hover_color, command=open_customer_management)
customer_management_button.grid(row=1, column=1, padx=20, pady=10)
customer_management_button.bind("<Enter>", lambda event: on_enter(customer_management_button))
customer_management_button.bind("<Leave>", lambda event: on_leave(customer_management_button))

backup_manager_button = tk.Button(button_frame, text="Backup Manager", font=button_font, width=20, height=2, relief="raised", 
                                  bg=button_color, activebackground=button_hover_color, command=backup_options)
backup_manager_button.grid(row=1, column=2, padx=20, pady=10)
backup_manager_button.bind("<Enter>", lambda event: on_enter(backup_manager_button))
backup_manager_button.bind("<Leave>", lambda event: on_leave(backup_manager_button))

# Help Label
help_label = tk.Label(window, text="Help", fg="blue", cursor="hand2", bg='#E6F0FF', font=("Arial", 10))
help_label.pack(side="bottom", anchor="se", padx=10, pady=10)
help_label.bind("<Button-1>", lambda e: show_help())

# Entry for PMB, only shown for Check-out
mailbox_label = tk.Label(window, text="Mailbox Number", bg='#E6F0FF')
mailbox_entry = tk.Entry(window)

# Hide PMB entry fields initially; they will appear only on "Check-out"
mailbox_label.pack_forget()
mailbox_entry.pack_forget()

# Run the Tkinter event loop
window.mainloop()
