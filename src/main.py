import sys
import customtkinter as ctk
from src.gui import App

if __name__ == "__main__":
    # Check for subprocess wrapper mode (for frozen executable)
    if len(sys.argv) > 1 and sys.argv[1] == '--esptool-wrapper':
        import esptool
        # Pass remaining arguments to esptool
        # sys.argv[0] is executable path, sys.argv[1] is wrapper flag
        # so we pass everything starting from index 2
        esptool.main(sys.argv[2:])
        sys.exit(0)

    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    
    app = App()
    app.mainloop()
