from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
import time
import pyautogui
import os

# CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCES_PANEL_IMG_PATH = (
    r"C:\Users\cyivs\OneDrive\Desktop\Spine_Project\HTML\static\Image\sources.png"
)
EXTENSION_IMG_PATH = r"C:\Users\cyivs\OneDrive\Desktop\Spine_Project\HTML\static\Image\resources_saver.png"

CHECKBOX_IMG_PATH = (
    r"C:\Users\cyivs\OneDrive\Desktop\Spine_Project\HTML\static\Image\checkbox.png"
)
SAVE_BUTTON_IMG_PATH = (
    r"C:\Users\cyivs\OneDrive\Desktop\Spine_Project\HTML\static\Image\save_button.png"
)

chrome_driver_path = r"E:\chromedriver-win64\chromedriver.exe"
extension_path = r"C:\Users\cyivs\OneDrive\Desktop\Spine_Project\HTML\pythonFile\Save-All-Resources-Chrome.crx"
game_url = r"https://slotcatalog.com/en/slots/Fortune-Tiger-PG-Soft"


def ExtensionPanelControl():
    # switch to ResourcesSaver panel
    extension_panel_pos = None
    try:
        extension_panel_pos = pyautogui.locateOnScreen(EXTENSION_IMG_PATH)
        if extension_panel_pos is not None:
            extension_panel_pos = pyautogui.center(extension_panel_pos)
            pyautogui.click(extension_panel_pos)
            pyautogui.click(extension_panel_pos)
            time.sleep(0.5)
            # click checkboxes
            checkboxes = None
            try:
                checkboxes = pyautogui.locateAllOnScreen(CHECKBOX_IMG_PATH)
                if checkboxes is not None:
                    for cb in checkboxes:
                        pos = pyautogui.center(cb)
                        pyautogui.click(pos)
                        time.sleep(0.5)
            except Exception as e:
                print(f"Failed to find checkbox: {e}")
        else:
            print("Failed to find extension panel")
    except Exception as e:
        print(f"Failed to find Extension panel with image: {e}")


def SourcesPanelControl():
    # switch to source panel
    source_panel_pos = None
    try:
        source_panel_pos = pyautogui.locateOnScreen(SOURCES_PANEL_IMG_PATH)
        if source_panel_pos is not None:
            # switch to Source panel and enable "Deactive breakpoints" (ctrl + F8)
            source_panel_pos = pyautogui.center(source_panel_pos)
            pyautogui.click(source_panel_pos)
            pyautogui.click(source_panel_pos)
            time.sleep(0.5)
            pyautogui.hotkey("ctrl", "f8")
            time.sleep(0.5)
        else:
            print("Failed to find Source panel")
    except Exception as e:
        print(f"Failed to find Source panel with image: {e}")


chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument("--auto-open-devtools-for-tabs")
chrome_options.add_argument(
    r"--user-data-dir=C:\Users\cyivs\AppData\Local\Google\Chrome\User Data"
)  # use own user setting
chrome_options.add_argument("--profile-directory=Profile 1")

service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# open chrome browser
driver.get(game_url)
driver.maximize_window()
time.sleep(3)

SourcesPanelControl()  # switch to Sources panel
ExtensionPanelControl()  # switch to ResourcesSaver panel
print("End Function Control\n")

# click button to start game
play_demo_button = driver.find_element(
    By.XPATH, '//*[@id="gameContainer"]/div/div/div/a'
)
play_demo_button.click()
time.sleep(10)

# click Save All Resource button
save_button = None
save_button = pyautogui.locateOnScreen(SAVE_BUTTON_IMG_PATH)
if save_button is not None:
    save_button = pyautogui.center(save_button)
    pyautogui.click(save_button)
    time.sleep(20)
else:
    print("Failed to find save button")
# unzip file
print("program end")
