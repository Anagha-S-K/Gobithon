from logging import root
import csv
import cv2
import pytesseract
import re
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pyzbar.pyzbar import decode
from PIL import Image, ImageDraw, ImageFont
from PIL import ImageOps
from datetime import datetime
import os
import tkinter as tk
from tkinter import messagebox, Toplevel, Scrollbar, Frame
from barcode import Code128
from barcode.writer import ImageWriter
import random
import tkinter as tk
from tkinter import font


# Load the customer data from the CSV file
customer_data = pd.read_csv(r'C:\notifynpick_final\customer.csv')

# Email configuration
sender_email = 'villagemail6@gmail.com'
sender_password = 'sqps ssqy rikp wlfd'

# Global variables for GUI to store mailbox, customer, and tracking details
mailbox_number = None
customer_name = None
customer_email = None
decoded_tracking_id = None  # To store the decoded tracking ID

# Path for the log file
log_file_path = 'history_log.csv'

# Function to extract text from a frame
def extract_text_from_frame(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(gray, config=custom_config)
    mailbox_number = re.findall(r'\d+', text)
    return mailbox_number[0] if mailbox_number else None

# Function to find customer details
def find_customer_details(mailbox_number):
    global customer_data
    # Reload the CSV file to ensure the latest data is used
    customer_data = pd.read_csv(r'C:\notifynpick_final\customer.csv')
    
    # Normalize column names: strip spaces and convert to lowercase
    customer_data.columns = customer_data.columns.str.strip().str.lower()

    # Check for a mailbox number match using the correct column name
    if 'mailbox number' not in customer_data.columns:
        raise KeyError("The column 'Mailbox Number' was not found in the CSV file. Check the column name.")

    matched_customer = customer_data[customer_data['mailbox number'] == int(mailbox_number)]
    
    if not matched_customer.empty:
        customer_name = matched_customer['customer name'].values[0]
        customer_email = matched_customer['email id'].values[0]
        return customer_name, customer_email
    else:
        return None, None


# Function to log history
def log_history(mailbox_number, customer_name, customer_email, tracking_number, carrier, unique_barcode, check_out_time=None):
    # Check if the log file exists
    if not os.path.exists(log_file_path):
        # If it doesn't exist, create the file with appropriate headers
        with open(log_file_path, 'w') as f:
            f.write("Mailbox Number,Customer Name,Customer Email,Tracking ID,Carrier,Unique Barcode,Check-in Time,Check-out Time\n")
    
    # Log the data
    with open(log_file_path, 'a') as f:
        check_in_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        check_out_time = check_out_time if check_out_time else "null"
        carrier = carrier if carrier else "null"
        tracking_number = tracking_number if tracking_number else "null"
        f.write(f"{mailbox_number},{customer_name},{customer_email},{tracking_number},{carrier},{unique_barcode},{check_in_time},{check_out_time}\n")




# Function to send email
def send_email():
    global customer_name, customer_email, decoded_tracking_id
    carrier = carrier_entry.get()
    if not customer_email:
        messagebox.showerror("Error", "Invalid email address. Cannot send email.")
        return

    # Prepare email body based on whether carrier or tracking ID is present
    subject = "You've Received a Mail from Village Mail & More!"
    body = f'''
    Dear {customer_name},

    We hope you're doing well! We wanted to let you know that you’ve received a new mail at *Village Mail & More*. Please stop by at your convenience to collect it, or let us know if you'd like to arrange a forwarding or delivery option.
    Mailbox Number: {mailbox_number}
    Your tracking ID is: {decoded_tracking_id if decoded_tracking_id else 'No Tracking ID'}
    Carrier: {carrier if carrier else 'Not provided'}
    Check in: {datetime.now().strftime('%m/%d/%Y at %H:%M:%S %p')}
    Feel free to reach out if you have any questions or need assistance.

    Thank you for choosing Village Mail & More!

    Best regards,
    Your Name
    Your Position
    Village Mail & More
    '''
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = customer_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, customer_email, msg.as_string())
       
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send email. Error: {e}")
    window.destroy()
# Function to generate a unique barcode for each ticket
def generate_unique_barcode():
    unique_id = str(random.randint(1000000000, 9999999999))
    barcode = Code128(unique_id, writer=ImageWriter())
    barcode_path = f'{unique_id}'
    barcode.save(barcode_path)
    return barcode_path, unique_id

# Function to print the label
def print_label():
    global mailbox_number, customer_name

    # Get the carrier and tracking number from the entry fields
    carrier = carrier_entry.get()
    tracking_number = tracking_id_entry.get()

    # Generate a unique barcode for the label
    barcode_path, unique_id = generate_unique_barcode()

    # Determine if we are using a carrier or tracking ID
    if carrier:
        tracking_number = "N/A"  # If a carrier is provided, we set tracking ID to null
    elif tracking_number:
        carrier = "N/A"  # If a tracking ID is provided, we set carrier to null

    # Log the details (with either carrier or tracking ID, and the generated unique barcode)
    log_history(mailbox_number, customer_name, customer_email, tracking_number, carrier, unique_id)

    # Create the label (as before, including the unique barcode)
    label = Image.new('RGB', (800, 800), color='white')
    draw = ImageDraw.Draw(label)
    font_large = ImageFont.truetype("times.ttf", 80)
    font_medium = ImageFont.truetype("times.ttf", 40)
    font_small = ImageFont.truetype("times.ttf", 30)

    draw.text((30, 30), "Mailbox", font=font_medium, fill='black')
    draw.text((30, 80), f"{mailbox_number}", font=font_large, fill='black')
    for x in range(20, 580, 10):
        draw.line((x, 200, x + 5, 200), fill='black', width=2)
    draw.text((30, 210), f"Mailbox: {mailbox_number}", font=font_medium, fill='black')
    draw.text((30, 330), f"{customer_name}", font=font_medium, fill='black')

    # Only print carrier if it was manually entered
    if carrier != "null":
        draw.text((30, 390), f"Carrier: {carrier}", font=font_small, fill='black')
    else:
        draw.text((30, 390), f"Carrier: {carrier}", font=font_small, fill='black')
    
        
    draw.text((30, 470), f"Tracking: {tracking_number}", font=font_small, fill='black')
    draw.text((30, 510), f"Received: {datetime.now().strftime('%m/%d/%Y %H:%M:%S %p')}", font=font_small, fill='black')

    # Insert the generated barcode image
    try:
        barcode_img = Image.open(barcode_path + ".png")
        label.paste(barcode_img, (30, 550))  # Paste barcode on the label
    except Exception as e:
        #print(f"Error loading barcode image: {e}")
        return

    # Save and show the label
    try:
        label_path = f'{mailbox_number}_label.png'
        label.save(label_path)
        label.show()
    except Exception as e:
        print(f"Error saving or showing the label: {e}")


def scan_tracking_id():
    global decoded_tracking_id
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        #print("Error: Unable to access the camera.")
        return
    

    #print("Scanning... Press 'q' to quit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            #print("Error: Failed to capture frame.")
            break

        # Display the video feed
        cv2.imshow("Scan Barcode - Press 'q' to capture", frame)

        # Detect barcodes
        barcodes = decode(frame)
        if barcodes:
            for barcode in barcodes:
                # Decode and update the tracking ID (any length or format)
                decoded_tracking_id = barcode.data.decode('utf-8')
                #print(f"Tracking ID: {decoded_tracking_id}")
                tracking_id_entry.delete(0, tk.END)
                tracking_id_entry.insert(0, decoded_tracking_id)

                # Disable Carrier field after successful scan
                carrier_entry.config(state=tk.DISABLED)
            break  # Exit the loop after successful detection

        # Quit on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            #print("Exiting scan...")
            break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()



# Function to capture mailbox number and scan tracking ID in one step
def capture_extract_and_notify():
    global mailbox_number, customer_name, customer_email
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Error", "Could not open video stream.")
        return
    while True:
        ret, frame = cap.read()
        if not ret:
            messagebox.showerror("Error", "Failed to grab frame")
            break
        cv2.imshow("Live Video - Press 'q' to capture mailbox", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            mailbox_number = extract_text_from_frame(frame)
            if mailbox_number:
                customer_name, customer_email = find_customer_details(mailbox_number)
                if customer_name and customer_email:
                    mailbox_entry.delete(0, tk.END)
                    mailbox_entry.insert(0, mailbox_number)
                    name_entry.delete(0, tk.END)
                    name_entry.insert(0, customer_name)
                    email_entry.delete(0, tk.END)
                    email_entry.insert(0, customer_email)
                  
            break
    cap.release()
    cv2.destroyAllWindows()


# Main window
#view_history():
    #if os.path.exists(log_file_path):
        #log_df = pd.read_csv(log_file_path)
        #history_window = Toplevel(window)
        #history_window.title("Check-in History")

        # Create a Scrollbar
        ##scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create a Frame for the history table
        #frame = Frame(history_window)
        #frame.pack(fill=tk.BOTH, expand=True)

        # Create a canvas for scrolling
        #canvas = tk.Canvas(frame)
        #canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure scrollbar
        #scrollbar.config(command=canvas.yview)
        #canvas.config(yscrollcommand=scrollbar.set)

        # Create a table-like layout using labels for each column
        #for i, column in enumerate(log_df.columns):
            #tk.Label(canvas, text=column, borderwidth=2, relief='groove').grid(row=0, column=i, sticky='nsew')

        # Insert each row of history
        #for row_idx, row in log_df.iterrows():
            #tk.Label(canvas, text=value, borderwidth=1, relief='groove').grid(row=row_idx + 1, column=col_idx, sticky='nsew')

        # Set column weight for resizing
        #for i in range(len(log_df.columns)):
            #canvas.grid_columnconfigure(i, weight=1)


# Main window
import tkinter as tk
from tkinter import font

# Create the main window
window = tk.Tk()
window.title("Village Mail & More")
window.geometry("800x600")
window.configure(bg='#E6F0FF')  # Light blue background


title_font = font.Font(family="Arial", size=24, weight="bold")
button_font = font.Font(family="Arial", size=12)

# Title Section
title_label = tk.Label(window, text="Village Mail & More", bg='#E6F0FF', fg="steelblue", font=title_font)
title_label.pack(pady=20)

# Define fonts
button_font = font.Font(family="Arial", size=12)

# Create a frame to hold the widgets
main_frame = tk.Frame(window, bg='#E6F0FF')
main_frame.pack(pady=20)

# Define button colors and hover effects in shades of blue
button_color = '#76b7f6'  # Default button color (blue)
button_hover_color = '#5fa8f0'  # Hover button color (darker blue)

# Function to change button color on hover
def on_enter(button):
    button['background'] = button_hover_color

def on_leave(button):
    button['background'] = button_color

# Create the entry fields with labels
tk.Label(main_frame, text="Mailbox Number", bg='#E6F0FF', font=button_font).pack(pady=4)
mailbox_entry = tk.Entry(main_frame, font=button_font, width=35)
mailbox_entry.pack(pady=5)

tk.Label(main_frame, text="Customer Name", bg='#E6F0FF', font=button_font).pack(pady=4)
name_entry = tk.Entry(main_frame, font=button_font, width=35)
name_entry.pack(pady=5)

tk.Label(main_frame, text="Email ID", bg='#E6F0FF', font=button_font).pack(pady=4)
email_entry = tk.Entry(main_frame, font=button_font, width=35)
email_entry.pack(pady=5)

tk.Label(main_frame, text="Carrier", bg='#E6F0FF', font=button_font).pack(pady=4)
carrier_entry = tk.Entry(main_frame, font=button_font, width=35)
carrier_entry.pack(pady=5)

tk.Label(main_frame, text="Tracking ID", bg='#E6F0FF', font=button_font).pack(pady=4)
tracking_id_entry = tk.Entry(main_frame, font=button_font, width=35)
tracking_id_entry.pack(pady=5)

# Create buttons with the original function names and reduced size
scan_package_button = tk.Button(main_frame, text="Scan Package", font=button_font, width=25, height=1, relief="raised", 
                                bg=button_color, activebackground=button_hover_color, command=capture_extract_and_notify)
scan_package_button.pack(pady=5)
scan_package_button.bind("<Enter>", lambda event: on_enter(scan_package_button))
scan_package_button.bind("<Leave>", lambda event: on_leave(scan_package_button))

scan_tracking_id_button = tk.Button(main_frame, text="Scan Tracking ID", font=button_font, width=25, height=1, relief="raised", 
                                    bg=button_color, activebackground=button_hover_color, command=scan_tracking_id)
scan_tracking_id_button.pack(pady=5)
scan_tracking_id_button.bind("<Enter>", lambda event: on_enter(scan_tracking_id_button))
scan_tracking_id_button.bind("<Leave>", lambda event: on_leave(scan_tracking_id_button))

print_label_button = tk.Button(main_frame, text="Print Label", font=button_font, width=25, height=1, relief="raised", 
                               bg=button_color, activebackground=button_hover_color, command=print_label)
print_label_button.pack(pady=5)
print_label_button.bind("<Enter>", lambda event: on_enter(print_label_button))
print_label_button.bind("<Leave>", lambda event: on_leave(print_label_button))

send_email_button = tk.Button(main_frame, text="Send Email", font=button_font, width=25, height=1, relief="raised", 
                              bg=button_color, activebackground=button_hover_color, command=send_email)
send_email_button.pack(pady=1)
send_email_button.bind("<Enter>", lambda event: on_enter(send_email_button))
send_email_button.bind("<Leave>", lambda event: on_leave(send_email_button))

# Run the Tkinter event loop
window.mainloop()
