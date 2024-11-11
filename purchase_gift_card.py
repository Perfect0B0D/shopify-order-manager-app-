import time
import hashlib
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException


# Replace with your actual API Key and API Secret
api_key = "9254a637-3062-4591-8159-0009565fb76d"
api_secret = "Li!4yIzY3xK)r81"


def generate_signature(api_key, api_secret):
    timestamp = str(int(time.time()))
    string_to_sign = api_key + api_secret + timestamp
    signature = hashlib.sha256(string_to_sign.encode('utf-8')).hexdigest()
    return signature, timestamp


def purchase_gift_card(shop_card_id, to_email):
    claim_code, pin_code, left_container_text, image_url = "", "", "", ""
    error_message = ""
    signature, timestamp = generate_signature(api_key, api_secret)
    purchase_params = {
        'shop_card_id': shop_card_id,
        'to_email': to_email,
        'api_key': api_key,
        'sig': signature
    }
    headers = {
        'x-sig-timestamp': timestamp,
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        print(f"Sending purchase request for card ID {shop_card_id} to {to_email}...")
        response = requests.post("https://apitest.gyft.com/mashery/v1/partner/purchase/gift_card_direct", 
                                 data=purchase_params, headers=headers)

        if response.status_code == 200:
            print("Purchase successful.")
            purchase_details = response.json()
            redemption_url = purchase_details.get('url')
            claim_code, pin_code, left_container_text, image_url, error_message = scrape_redemption_url(redemption_url)
            return claim_code, pin_code, left_container_text, image_url, error_message
        else:
            error_message = f"Error purchasing gift card: {response.status_code} - {response.text}"
            return claim_code, pin_code, left_container_text, image_url, error_message

    except requests.exceptions.RequestException as e:
        error_message = f"RequestException during purchase: {e}"
        return claim_code, pin_code, left_container_text, image_url, error_message
def initialize_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver


def wait_for_page_load(driver, timeout=1, error_message = ""):
    try:
        wait = WebDriverWait(driver, timeout)
        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        print("Page loaded successfully.")
    except TimeoutException:
        print("Timeout waiting for page to load.")
        error_message = f"Timeout waiting for page to load."
        driver.quit()
    return error_message


def click_view_button(driver, error_message = ""):
    try:
        view_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@class="my-gift-card-prereveal"]/button'))
        )
        view_button.click()
        print("Clicked 'View Gift Code' button.")
        time.sleep(7)  # Wait for the page to respond
    except (NoSuchElementException, TimeoutException) as e:
        print(f"Error clicking 'View Gift Code' button: {e}")
        error_message = f"Error clicking 'View Gift Code' button: {e}"
    return error_message


def get_claim_and_pin_codes(driver, error_message = ""):
    claim_code, pin_code, left_container_text = "", "", ""
    try:
        claim_code_element = driver.find_element(By.XPATH, 
                                                 "//main/aside/div[@class='my-gift-card-reveal']/div[@class='my-fields-group']/div[@class='my-field']/div[@class='my-value ng-binding']")
        claim_code = claim_code_element.text
        print("Claim Code:", claim_code)
    except NoSuchElementException:
        print("Claim code not found.")
        error_message = f"Claim code not found."
    try:
        pin_code_element = driver.find_element(By.XPATH, 
                                               "//main/aside/div[@class='my-gift-card-reveal']/div[@class='my-fields-group']/div[@class='my-field ng-scope']/div[@class='my-value ng-binding']")
        pin_code = pin_code_element.text
        print("PIN Code:", pin_code)
    except NoSuchElementException:
        print("Pin code not found.")
    
    try:
        left_container = driver.find_element(By.XPATH, "//div[@class='my-content clearfix']")
        left_container_text = left_container.text
        print("left_container text====>", left_container_text)
    except NoSuchElementException:
        print("left container not found.")
    return claim_code, pin_code, left_container_text, error_message



def get_image_url(driver, error_message = ""):
    try:
        image_element = WebDriverWait(driver, 1).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.my-gift-card-image img.my-image'))
        )
        image_url = image_element.get_attribute('src')
        print("Image URL:", image_url)
        return image_url, error_message
    except (NoSuchElementException, TimeoutException) as e:
        print(f"Error fetching image URL: {e}")
        error_message = f"Error fetching image URL: {e}"
        return "", error_message


def scrape_redemption_url(url, error_message = ""):
    driver = initialize_driver()
    driver.get(url)
    error_message = wait_for_page_load(driver, error_message=error_message)
    if error_message:
        driver.quit()
        return "", "", "", "", error_message

    error_message = click_view_button(driver, error_message=error_message)
    if error_message:
        driver.quit()
        return "", "", "", "", error_message

    claim_code, pin_code, left_container_text, error_message = get_claim_and_pin_codes(driver, error_message)
    if error_message:
        driver.quit()
        return "", "", "", "", error_message

    image_url, error_message = get_image_url(driver, error_message=error_message)
    driver.quit()

    return claim_code, pin_code, left_container_text, image_url, error_message


