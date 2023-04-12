#this is a script to copy files from a hyperdecks

import os
import concurrent.futures
import hashlib
import tempfile
import shutil
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from ftplib import FTP
import time

# Define the FTP login credentials
ftp_user = 'anonymous'
ftp_password = ''

# Define the FTP folder path for each HyperDeck recorder
hyperdeck_folders = {
    '10.10.2.10': '/1',
    '10.10.2.11': '/1',
    '10.10.2.12': '/1',
    '10.10.2.13': '/1',
    '10.10.2.14': '/usb/HYPERDECK 5',
    '10.10.2.15': '/usb/HYPERDECK 6'
}

def calculate_checksum(file_path):
    with open(file_path, 'rb') as f:
        file_data = f.read()
    return hashlib.md5(file_data).hexdigest()

def download_latest_file(ip_address, folder):
    try:
        # Connect to the FTP server
        ftp = FTP(ip_address)
        ftp.login(user=ftp_user, passwd=ftp_password)

        # Change to the correct directory
        ftp.cwd(folder)

        # Get a list of files in the directory
        files = ftp.nlst()

        # Sort the files by creation date
        sorted_files = sorted(files, key=lambda file: ftp.sendcmd('MDTM {}'.format(file))[4:], reverse=True)

        if len(sorted_files) > 0:
            # Get the latest file
            latest_file = sorted_files[0]

            # Download the remote file data into memory
            remote_file_data = bytearray()
            ftp.retrbinary('RETR {}'.format(latest_file), remote_file_data.extend)

            # Calculate the remote file checksum
            remote_file_checksum = hashlib.md5(remote_file_data).hexdigest()

            # Check if the file already exists in the local folder
            file_path = os.path.join(local_folder_path, latest_file)
            if os.path.isfile(file_path):
                # Calculate the local file checksum
                local_file_checksum = calculate_checksum(file_path)

                # Compare local and remote file checksums
                if local_file_checksum == remote_file_checksum:
                    print("File {} already exists in the local folder and has the same checksum.".format(latest_file))
                    ftp.quit()
                    return

                # Append a number to the file name if it already exists and has a different checksum
                i = 1
                while True:
                    new_file_path = os.path.join(local_folder_path, '{}_{}.{}'.format(os.path.splitext(latest_file)[0], i, os.path.splitext(latest_file)[1]))
                    if not os.path.isfile(new_file_path):
                        file_path = new_file_path
                        break
                    i += 1
                print("File {} already exists in the local folder, saving as {}".format(latest_file, os.path.basename(file_path)))

            # Save the remote file data to a temporary file
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(remote_file_data)
                temp_file_path = temp_file.name

            # Move the temporary file to the final destination
            shutil.move(temp_file_path, file_path)

            print("Downloaded file {} from {} to {}".format(latest_file, ip_address, file_path))

        else:
            print("No files found in directory {} on {}".format(folder, ip_address))

        # Disconnect from the FTP server
        ftp.quit()

    except Exception as e:
        print("An error occurred while downloading the file from {}: {}".format(ip_address, e))

    
    
def start_download():
    global local_folder_path
    
    local_folder_path = filedialog.askdirectory(title="Select folder to save files")
    
    if not local_folder_path:
        status_label.config(text="No folder selected. Please select a destination folder to start the download.")
        return

    status_label.config(text="Downloading files...")
    start_button.config(state='disabled')

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(download_latest_file, ip_address, folder) for ip_address, folder in hyperdeck_folders.items()]
        concurrent.futures.wait(futures)

    status_label.config(text="Download complete. Closing in 5 seconds.")
    root.after(5000, root.quit)


# Create the main window
root = tk.Tk()
root.title("File Downloader")

# Create a frame for the content
content = ttk.Frame(root, padding=(10, 10, 10, 10))
content.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Create the button to start the download process
start_button = ttk.Button(content, text="Select Destination Folder and Start Download", command=start_download)
start_button.grid(row=0, column=0, pady=(0, 10))

# Create the label to display the status
status_label = ttk.Label(content, text="Please select a destination folder to start the download.")
status_label.grid(row=1, column=0)

# Run the main event loop
root.mainloop()


