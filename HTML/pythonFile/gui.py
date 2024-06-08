import pyautogui
import time

# Print the current mouse position continuously
try:
    while True:
        x, y = pyautogui.position()
        print(f"Mouse position: ({x}, {y})", end="\r")
        time.sleep(0.5)  # Update every 0.1 seconds
except KeyboardInterrupt:
    print("\nProcess interrupted by user.")
