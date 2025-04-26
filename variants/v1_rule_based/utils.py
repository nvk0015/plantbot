from datetime import datetime
import subprocess
import logging


def find_time():
    c = datetime.now()

    # return current time
    return c.strftime('%H:%M')

logging.basicConfig(filename='plant_interface.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

def speak_text(text):
    """Speak the provided text using `espeak`."""
    try:
        safe_text = text.replace("'", "\\'")
        subprocess.run(["espeak", safe_text], check=True)
    except subprocess.CalledProcessError:
        logging.error("Failed to execute espeak.")


def main():
    current_time = find_time()

    return current_time

if __name__ == "__main__":
    main()