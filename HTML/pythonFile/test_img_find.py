import pyautogui
import time

# Path to the gif_radio_button.png image
GIF_BUTTON_IMG_PATH = (
    "C:\\Users\\cyivs\\OneDrive\\Desktop\\VSCode\\HTML\\static\\Image\\gif_button.png"
)

# Give some time to manually open the window and ensure it is visible
print("You have 5 seconds to bring the window with the GIF button to the front.")
time.sleep(5)

# Locate and click the GIF radio button using an image
gif_button_location = pyautogui.locateOnScreen(GIF_BUTTON_IMG_PATH)
if gif_button_location is not None:
    print("GIF radio button found.")
    gif_button_location = pyautogui.center(gif_button_location)
    pyautogui.click(gif_button_location)
else:
    print("GIF radio button not found.")
