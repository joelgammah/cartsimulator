# simulator.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import logging
from product import PRODUCTS   # import product list
from brands import zara_handler, hm_handler  # import the Zara handler module

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_browser():
    chrome_options = Options()
    # Uncomment for headless mode
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--window-size=1920,1080')
    return webdriver.Chrome(options=chrome_options)

def process_product(driver, product):
    brand = product.get("brand", "default").lower()
    if brand == "zara":
        logger.info("Using Zara handler.")
        return zara_handler.add_to_cart(driver, product)
    elif brand == "h&m":
        logger.info("Using H&M handler.")
        return hm_handler.add_to_cart(driver, product)
    else:
        logger.error(f"No handler implemented for brand: {brand}")
        return False

def main():
    driver = setup_browser()
    try:
        for product in PRODUCTS:
            logger.info(f"Processing product: {product}")
            if process_product(driver, product):
                time.sleep(3)  # Wait between product additions
    finally:
        input("Automation complete. Press Enter to close the browser...")
        driver.quit()

if __name__ == "__main__":
    main()
