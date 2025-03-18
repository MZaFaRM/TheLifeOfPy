from src.nature import Nature

import platform

def main():
    """Main entry point for the application."""
    if platform.system() == "Windows":
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()

    env = Nature()
    env.run()

if __name__ == "__main__":
    main()
