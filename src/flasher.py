import sys
import threading
import serial.tools.list_ports
import esptool
import time
import re
from io import StringIO

class FlasherInterface:
    def __init__(self, port, firmware_path, baud_rate=460800, chip_type="auto", callback=None):
        self.port = port
        self.firmware_path = firmware_path
        self.baud_rate = baud_rate
        self.chip_type = chip_type
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
        """Runs the esptool flashing process in a separate subprocess."""
        self.is_flashing = True
        self.cancel_requested = False
        
        def run():
            try:
                self.log(f"Starting flash on {self.port} at {self.baud_rate} baud...\n")
                
                # Wait 3 seconds before performing reset
                self.log("Waiting 3 seconds before reset...\n")
                time.sleep(3)
                
                import subprocess
                
                # Build command for subprocess
                if getattr(sys, 'frozen', False):
                    # We are running as a frozen executable (PyInstaller)
                    # Use our special wrapper flag to invoke esptool within our own process exe
                    # but as a separate subprocess
                    cmd = [sys.executable, '--esptool-wrapper']
                else:
                    # Running from source
                    cmd = [sys.executable, '-m', 'esptool']

                cmd.extend([
                    '--port', self.port,
                    '--baud', str(self.baud_rate),
                    '--before', 'default-reset',
                    '--after', 'hard-reset',
                ])
                
                # Add chip type if specified
                if self.chip_type and self.chip_type != "auto":
                    cmd.extend(['--chip', self.chip_type])
                
                cmd.extend([
                    'write-flash',
                    '-z',
                    '--flash-mode', 'keep',
                    '--flash-freq', 'keep',
                    '--flash-size', 'keep',
                    '0x0', self.firmware_path
                ])
                
                # Log the command for debugging
                self.log(f"Running command: {' '.join(cmd)}\n")
                
                try:
                    # Run esptool as subprocess
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1
                    )
                    
                    # Read output character by character to handle \r progress bars correctly
                    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                    verified_msg_shown = False
                    current_line = []
                    
                    while True:
                        char = process.stdout.read(1)
                        if not char:
                            break
                        
                        if char == '\r' or char == '\n':
                            # Process the complete chunk/line
                            line_str = ''.join(current_line)
                            clean_line = ansi_escape.sub('', line_str)
                            
                            # Log it (add newline if it was a \r update to keep log readable if needed, 
                            # or just pass it through. GUI log likely handles \n best)
                            if char == '\r':
                                # If it's a progress update, we might want to overwrite or just append
                                # For simplicity in this text box, we'll just append
                                pass 
                            
                            self.log(clean_line + ('\n' if char == '\n' else ''))
                            
                            # Check for 100% trigger
                            if not verified_msg_shown and "100" in clean_line and "%" in clean_line:
                                self.log("\nVerifying upload (this may take a moment)...\n")
                                verified_msg_shown = True
                            
                            current_line = []
                        else:
                            current_line.append(char)
                    
                    process.wait()
                    
                    if process.returncode == 0:
                        self.log("\nFlashing completed successfully!\n")
                    else:
                        self.log(f"\nError during flashing (exit code: {process.returncode})\n")
                        
                except Exception as e:
                    self.log(f"\nError during flashing: {str(e)}\n")
                finally:
                    self.is_flashing = False
                    
            except Exception as e:
                self.log(f"Unexpected error: {str(e)}")
                self.is_flashing = False

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
