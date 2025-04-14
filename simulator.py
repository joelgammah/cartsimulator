from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
from product import PRODUCTS  # Import the product list

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_browser():
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # Uncomment for headless mode
    chrome_options.add_argument('--window-size=1920,1080')
    return webdriver.Chrome(options=chrome_options)

def add_to_cart(driver, product):
    """
    Adds a product to the cart.
    
    product: dict with keys:
      - "url": URL of the product page
      - "variant": desired variant (e.g., size) or None if not applicable.
    """
    url = product["url"]
    variant = product.get("variant")
    
    try:
        logger.info(f"Processing: {url}")
        driver.get(url)
        
        # Wait for and click the "Add to Cart" button.
        add_to_cart_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@data-qa-action='add-to-cart']"))
        )
        add_to_cart_button.click()
        logger.info(f"Clicked Add to Cart for: {url}")
        
        # Handle variant selection if a variant (like a size) is specified.
        if variant:
            # Construct an XPath for the variant option.
            # This example targets a <div> with an attribute and text containing the variant.
            size_option_xpath = (
                f"//div[@data-qa-qualifier='size-selector-sizes-size-label' and contains(text(), '{variant}')]"
            )
            size_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, size_option_xpath))
            )
            size_option.click()
            logger.info(f"Selected variant '{variant}' for: {url}")
        else:
            logger.info("No variant specified; skipping variant selection.")
        
        # Wait a bit for the cart to update.
        time.sleep(2)
        
        # Verify the product was added by checking the cart count element.
        confirmation = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//span[@data-qa-id='layout-header-go-to-cart-items-count']"))
        )
        cart_count = confirmation.text.strip()
        if cart_count and int(cart_count) > 0:
            logger.info(f"Successfully added product to cart; cart count: {cart_count}")
            return True
        else:
            logger.error("Cart count did not update as expected.")
            return False
        
    except Exception as e:
        logger.error(f"Failed to add product from {url}: {str(e)}")
        return False

def main():
    driver = setup_browser()
    try:
        # Loop over each product in the PRODUCTS list.
        for product in PRODUCTS:
            if add_to_cart(driver, product):
                time.sleep(3)  # Wait between product additions for stability.
    finally:
        input("Automation complete. Press Enter to close the browser...")
        driver.quit()

if __name__ == "__main__":
    main()
