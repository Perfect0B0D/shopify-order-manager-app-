import time
import hashlib
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# test flag setting

test_flag = False



if test_flag:
    api_key = "9254a637-3062-4591-8159-0009565fb76d"
    api_secret = "Li!4yIzY3xK)r81"
else:
    api_key = "8b7d9974-4094-42c9-a71b-407145b72661"
    api_secret = "u{Ow1tJ)UuJKi30"
    
    


def generate_signature(api_key, api_secret):
    timestamp = str(int(time.time()))
    string_to_sign = api_key + api_secret + timestamp
    signature = hashlib.sha256(string_to_sign.encode('utf-8')).hexdigest()
    return signature, timestamp


def purchase_gift_card(shop_card_id, to_email):
    claim_code, pin_code, left_container_text, image_url, redemption_url = "", "", "", "", ""
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
      
        if test_flag:
             response = requests.post("https://apitest.gyft.com/mashery/v1/partner/purchase/gift_card_direct", 
                                 data=purchase_params, headers=headers)
        else:
             response = requests.post("https://api.gyft.com/mashery/v1/partner/purchase/gift_card_direct", 
                                 data=purchase_params, headers=headers)

        if response.status_code == 200:
            purchase_details = response.json()
            redemption_url = purchase_details.get('url')
            # print("redemption_url==========>", redemption_url)
            claim_code, pin_code, left_container_text, image_url, error_message = get_claim_and_pin_codes(redemption_url)
            return claim_code, pin_code, left_container_text, image_url, error_message, redemption_url
        else:
            error_message = f"Error purchasing gift card: {response.status_code} - {response.text}"
            return claim_code, pin_code, left_container_text, image_url, error_message, redemption_url

    except requests.exceptions.RequestException as e:
        error_message = f"RequestException during purchase: {e}"
        return claim_code, pin_code, left_container_text, image_url, error_message, redemption_url

def get_claim_and_pin_codes(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    
    claim_code, pin_code, left_container_text, image_url, error_message = "", "", "", "", ""
    #page load and wait untill loaded
    
    
    try:
        driver.get(url)
        WebDriverWait(driver, 50).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='my-gift-card-image']"))
          )
        # Wait for the 'view gift code' button to be clickable and then click it
        try:
            view_gift_code_btn = WebDriverWait(driver, 50).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@class="my-gift-card-prereveal"]/button'))
            )
            view_gift_code_btn.click()
        except TimeoutException:
            print("View Gift Button not found, skipping")
        
        WebDriverWait(driver, 50).until(
            EC.visibility_of_element_located((By.XPATH, "//main/aside/div[@class='my-gift-card-reveal']/div[@class='my-fields-group']/div[@class='my-field']/div[@class='my-value ng-binding']"))
        )

        # Wait for the page content to load
        
        WebDriverWait(driver, 50).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.my-gift-card-image img.my-image'))
        )

        # Extract the image URL
        try:
            image_element = driver.find_element(By.CSS_SELECTOR, 'div.my-gift-card-image img.my-image')
            image_url = image_element.get_attribute('src')
            print("Image URL:", image_url)
        except NoSuchElementException:
            error_message = f"Error fetching image URL."

        # Extract claim code
        try:
            claim_code_element = driver.find_element(By.XPATH, 
                                                     "//main/aside/div[@class='my-gift-card-reveal']/div[@class='my-fields-group']/div[@class='my-field']/div[@class='my-value ng-binding']")
            claim_code = claim_code_element.text
            print("Claim Code:", claim_code)
        except NoSuchElementException:
            error_message = f"Claim code not found."

        # Extract pin code
        try:
            pin_code_element = driver.find_element(By.XPATH, 
                                                   "//main/aside/div[@class='my-gift-card-reveal']/div[@class='my-fields-group']/div[@class='my-field ng-scope']/div[@class='my-value ng-binding']")
            pin_code = pin_code_element.text
            print("PIN Code:", pin_code)
        except NoSuchElementException:
            print(f"Pin code not found.")

        # Extract additional left container text
        try:
            left_container = driver.find_element(By.XPATH, "//div[@class='my-content clearfix']")
            left_container_text = left_container.text
            print("left_container text====>", left_container_text)
        except NoSuchElementException:
            error_message = f"Left container text not found."

    except TimeoutException as e:
        error_message = f"Timeout error: {str(e)}"
        
    driver.quit()  

    return claim_code, pin_code, left_container_text, image_url, error_message





