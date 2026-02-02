import customtkinter as ctk
from tkinter import filedialog
from src.flasher import FlasherInterface
import threading
import sys
import queue

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ESP32 Firmware Flasher")
        self.geometry("600x500")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)


        self.flasher = FlasherInterface(None, None)
        self.firmware_path = None
        
        # UI Elements
        self.create_widgets()
        
        # Port Auto-refresh
        self.refresh_ports()
        
        # Queue for thread-safe logging
        self.log_queue = queue.Queue()
        self.check_log_queue()


    def create_widgets(self):
        # 1. Port Selection
        self.port_frame = ctk.CTkFrame(self)
        self.port_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        self.port_label = ctk.CTkLabel(self.port_frame, text="Serial Port:")
        self.port_label.pack(side="left", padx=10)
        
        self.port_option_menu = ctk.CTkOptionMenu(self.port_frame, values=["Scanning..."])
        self.port_option_menu.pack(side="left", padx=10, expand=True, fill="x")
        
        self.refresh_btn = ctk.CTkButton(self.port_frame, text="Refresh", width=80, command=self.refresh_ports)
        self.refresh_btn.pack(side="right", padx=10)

        # 1b. Baud Rate Selection
        self.baud_label = ctk.CTkLabel(self.port_frame, text="Baud Rate:")
        self.baud_label.pack(side="left", padx=10)

        self.baud_rates = ["300", "600", "1200", "2400", "4800", "9600", "14400", "19200", 
                          "28800", "38400", "57600", "115200", "230400", "460800", "921600", 
                          "1000000", "2000000"]
        self.baud_option_menu = ctk.CTkOptionMenu(self.port_frame, values=self.baud_rates, width=90)
        self.baud_option_menu.pack(side="left", padx=5)
        self.baud_option_menu.set("460800")
        
        # 1c. Chip Type Selection
        self.chip_label = ctk.CTkLabel(self.port_frame, text="Chip:")
        self.chip_label.pack(side="left", padx=(10, 5))
        
        self.chip_types = ["auto", "esp32", "esp32s2", "esp32s3", "esp32c3", "esp32c6", "esp32h2"]
        self.chip_option_menu = ctk.CTkOptionMenu(self.port_frame, values=self.chip_types, width=90)
        self.chip_option_menu.pack(side="left", padx=5)
        self.chip_option_menu.set("auto")


        # 2. File Selection
        self.file_frame = ctk.CTkFrame(self)
        self.file_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.file_label = ctk.CTkLabel(self.file_frame, text="Firmware (*.merged.bin):")
        self.file_label.pack(side="left", padx=10)
        
        self.file_path_entry = ctk.CTkEntry(self.file_frame, placeholder_text="No file selected")
        self.file_path_entry.pack(side="left", padx=10, expand=True, fill="x")
        
        self.browse_btn = ctk.CTkButton(self.file_frame, text="Browse", width=80, command=self.browse_file)
        self.browse_btn.pack(side="right", padx=10)

        # 3. Action Buttons
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        
        self.flash_btn = ctk.CTkButton(self.action_frame, text="Flash Firmware", command=self.start_flashing, height=40)
        self.flash_btn.pack(fill="x")

        # 4. Console/Log
        self.log_textbox = ctk.CTkTextbox(self, state="disabled")
        self.log_textbox.grid(row=3, column=0, padx=20, pady=(10, 20), sticky="nsew")


    def refresh_ports(self):
        ports = self.flasher.list_ports()
        if not ports:
            self.port_option_menu.configure(values=["No ports found"])
            self.port_option_menu.set("No ports found")
        else:
            self.port_option_menu.configure(values=ports)
            self.port_option_menu.set(ports[0])

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Merged Binaries", "*.merged.bin"), ("All Binary Files", "*.bin")])
        if filename:
            self.firmware_path = filename
            self.file_path_entry.delete(0, "end")
            self.file_path_entry.insert(0, filename)

    def log_callback(self, message):
        self.log_queue.put(message)

    def check_log_queue(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get()
            self.log_textbox.configure(state="normal")
            self.log_textbox.insert("end", msg)
            self.log_textbox.see("end")
            self.log_textbox.configure(state="disabled")
        
        self.after(100, self.check_log_queue)

    def start_flashing(self):
        port = self.port_option_menu.get()
        if port == "No ports found" or port == "Scanning...":
            self.log_callback("Error: No valid serial port selected.\n")
            return
        
        if not self.firmware_path:
            self.log_callback("Error: No firmware file selected.\n")
            return

        self.flash_btn.configure(state="disabled")
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
        
        # Initialize flasher with selected options
        try:
            baud_rate = int(self.baud_option_menu.get())
        except ValueError:
            baud_rate = 460800 # Default fallback
            
        self.flasher = FlasherInterface(
            port, 
            self.firmware_path, 
            baud_rate=baud_rate, 
            chip_type=self.chip_option_menu.get(), 
            callback=self.log_callback
        )

        
        # Start in thread
        self.flasher.flash_firmware()
        
        # Monitor completion to re-enable button
        self.monitor_thread = threading.Thread(target=self.wait_for_completion, daemon=True)
        self.monitor_thread.start()

    def wait_for_completion(self):
        while self.flasher.is_flashing:
            time.sleep(0.1)
        self.flash_btn.configure(state="normal")

import time
