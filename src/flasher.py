import sys
import threading
import serial.tools.list_ports
import esptool
import time
import re
from io import StringIO

class FlasherInterface:
    def __init__(self, port, firmware_path, baud_rate=460800, callback=None):
        self.port = port
        self.firmware_path = firmware_path
        self.baud_rate = baud_rate
        self.callback = callback
        self.is_flashing = False
        self.cancel_requested = False

    def list_ports(self):
        """Returns a list of available serial ports."""
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def log(self, message):
        """Send log message to callback."""
        if self.callback:
            self.callback(message)

    def flash_firmware(self):
        """Runs the esptool flashing process in a separate thread."""
        self.is_flashing = True
        self.cancel_requested = False
        
        def run():
            try:
                self.log(f"Starting flash on {self.port} at {self.baud_rate} baud...\n")
                
                # Mock args for esptool
                # We need to simulate the command line arguments
                # esptool.py -p PORT -b BAUD write_flash -z 0x0 FIRMWARE_PATH
                
                # We'll use esptool.main() but we need to capture stdout/stderr
                # or rely on subclassing/stubbing if esptool doesn't support easy programmatic use with callbacks.
                # Fortunately, esptool is python.
                
                # Redirect stdout/stderr to capture output
                original_stdout = sys.stdout
                original_stderr = sys.stderr
                
                
                class StreamLogger:
                    def __init__(self, callback):
                        self.callback = callback
                        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                    
                    def write(self, text):
                        # Strip ANSI codes
                        clean_text = self.ansi_escape.sub('', text)
                        # Fix line breaks for GUI (convert \r to \n)
                        clean_text = clean_text.replace('\r\n', '\n').replace('\r', '\n')
                        if clean_text:
                            self.callback(clean_text)
                            
                    def flush(self):
                        pass

                sys.stdout = StreamLogger(self.callback)
                sys.stderr = StreamLogger(self.callback)

                args = [
                    '--port', self.port,
                    '--baud', str(self.baud_rate),
                    '--before', 'default-reset',
                    '--after', 'hard-reset',
                    'write-flash',
                    '-z',
                    '0x0', self.firmware_path
                ]
                
                try:
                    esptool.main(args)
                    self.log("\nFlashing completed successfully!\n")
                except Exception as e:
                    self.log(f"\nError during flashing: {str(e)}\n")
                finally:
                    sys.stdout = original_stdout
                    sys.stderr = original_stderr
                    self.is_flashing = False
                    
            except Exception as e:
                self.log(f"Unexpected error: {str(e)}")
                self.is_flashing = False

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
