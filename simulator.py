import os
import time
import json
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from product import PRODUCTS
from brands import zara_handler, hm_handler, generic_handler  # Import your handlers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config():
    """
    Loads the central configuration from config.json located at the project root.
    """
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r") as f:
        return json.load(f)

def setup_browser():
    """
    Initializes and returns the Selenium Chrome WebDriver.
    """
    chrome_options = Options()
    # Uncomment the next line for headless mode if desired:
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--window-size=1920,1080')
    return webdriver.Chrome(options=chrome_options)

# Mapping brand names to their handler functions.
BRAND_HANDLERS = {
    "zara": zara_handler.add_to_cart,
    "h&m": hm_handler.add_to_cart,
    # For every other brand, default to the generic handler.
    "generic": generic_handler.add_to_cart
}

def process_brand_products(driver, brand, products, central_config):
    """
    Processes all products for a given brand in a new browser tab.
    
    :param driver: Selenium WebDriver instance.
    :param brand: The brand name.
    :param products: List of product dictionaries for the brand.
    :param central_config: Central configuration dictionary.
    """
    logger.info(f"Processing brand: {brand} with {len(products)} product(s)")
    # Open a new tab for this brand.
    driver.execute_script("window.open('');")
    new_tab = driver.window_handles[-1]
    driver.switch_to.window(new_tab)
    
    # Get the handler function; if not defined for this brand, use generic.
    handler = BRAND_HANDLERS.get(brand, BRAND_HANDLERS["generic"])
    
    for product in products:
        logger.info(f"Processing product: {product}")
        # Pass central_config to the handler.
        result = handler(driver, product, central_config)
        logger.info(f"Result for {product.get('name', 'Unknown')}: {result}")
        time.sleep(3)
        
    # Optionally, close the tab after processing:
    # driver.close()
    # driver.switch_to.window(driver.window_handles[0])

def group_products_by_brand(products):
    """
    Groups products by their brand (converts brand to lowercase).
    
    :param products: List of product dictionaries.
    :return: Dictionary mapping brands to lists of products.
    """
    brand_products = {}
    for product in products:
        brand = product.get("brand", "generic").lower()
        brand_products.setdefault(brand, []).append(product)
    return brand_products

def main():
    """
    Main function: sets up the browser, loads the configuration,
    groups products by brand, and processes each brand in separate tabs.
    """
    driver = setup_browser()
    central_config = load_config()
    try:
        brand_products = group_products_by_brand(PRODUCTS)
        for brand, products in brand_products.items():
            process_brand_products(driver, brand, products, central_config)
        input("Automation complete. Press Enter to close the browser...")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
