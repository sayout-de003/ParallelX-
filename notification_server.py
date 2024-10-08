import tkinter as tk
from tkinter import messagebox  # Import messagebox here
from flask import Flask, request, jsonify
import threading
import subprocess
import webbrowser 

app = Flask(__name__)

# Create a global Tkinter root instance
root = tk.Tk()
root.withdraw()  # Hide the main window initially

def show_notification(message):
    # Function to show a pop-up notification
    messagebox.showinfo("Notification", message)
    webbrowser.open('http://localhost:8000/notification')
    # Use 'start' on Windows
 # Use messagebox here

@app.route('/notify', methods=['POST'])
def notify():
    data = request.json
    print(f"Notification received: {data['message']}")
    
    # Schedule the notification function to run on the main thread
    root.after(0, show_notification, data['message'])

    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    # Run the Flask server in a separate thread
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5001)).start()
    
    # Start the Tkinter main loop
    root.mainloop()
