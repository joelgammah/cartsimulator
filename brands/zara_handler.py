# brands/zara_handler.py
import json
import os
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

# Load the central configuration from the project root.
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
with open(CONFIG_PATH, "r") as f:
    CENTRAL_CONFIG = json.load(f)

def get_zara_config():
    """
    Returns Zara-specific configuration, or falls back to the default configuration.
    """
    return CENTRAL_CONFIG.get("zara", CENTRAL_CONFIG["default"])

def add_to_cart(driver, product):
    """
    Adds a Zara product to the shopping cart using the centralized configuration.
    
    :param driver: Selenium WebDriver instance.
    :param product: Dictionary with keys "name", "url", and optionally "variant".
    :return: True if the product was successfully added, else False.
    """
    url = product["url"]
    name = product.get("name", "Unknown Product")
    variant = product.get("variant")
    
    # Use the helper to get the configuration for Zara
    config = get_zara_config()
    timeouts = config.get("timeouts", {})
    timeout_default = timeouts.get("default", 10)
    timeout_variant = timeouts.get("variant", 10)
    
    try:
        logger.info(f"[ZARA] Processing product: {name} ({url})")
        driver.get(url)
        
        # Use the Zara configuration directly for the add-to-cart button XPath.
        add_to_cart_xpath = config["add_to_cart_button_xpath"]
        logger.info(f"[ZARA] Waiting for Add to Cart button using XPath: {add_to_cart_xpath}")
        add_to_cart_button = WebDriverWait(driver, timeout_default).until(
            EC.element_to_be_clickable((By.XPATH, add_to_cart_xpath))
        )
        add_to_cart_button.click()
        logger.info(f"[ZARA] Clicked Add to Cart for: {name}")
        
        # If a variant is specified, select it.
        if variant:
            size_option_xpath = config["size_option_xpath_template"].replace("{variant}", variant)
            logger.info(f"[ZARA] Waiting for size option using XPath: {size_option_xpath}")
            try:
                size_option = WebDriverWait(driver, timeout_variant).until(
                    EC.element_to_be_clickable((By.XPATH, size_option_xpath))
                )
                size_option.click()
                logger.info(f"[ZARA] Selected variant '{variant}' for: {name}")
            except Exception as inner_e:
                logger.error(f"[ZARA] Failed to select variant '{variant}': {inner_e}")
                screenshot_path = os.path.join(os.getcwd(), f"{name.replace(' ', '_')}_size_error.png")
                driver.save_screenshot(screenshot_path)
                logger.error(f"[ZARA] Screenshot saved to: {screenshot_path}")
                return False
        else:
            logger.info("[ZARA] No variant specified; skipping size selection.")
        
        # Pause to allow cart update.
        time.sleep(2)
        
        cart_count_xpath = config["cart_count_xpath"]
        logger.info(f"[ZARA] Waiting for cart count element using XPath: {cart_count_xpath}")
        cart_count_element = WebDriverWait(driver, timeout_default).until(
            EC.presence_of_element_located((By.XPATH, cart_count_xpath))
        )
        cart_count = cart_count_element.text.strip()
        logger.info(f"[ZARA] Cart count found: '{cart_count}'")
        
        if cart_count and int(cart_count) > 0:
            logger.info(f"[ZARA] Successfully added product; cart count: {cart_count}")
            return True
        else:
            logger.error("[ZARA] Cart count did not update as expected.")
            return False
    
    except Exception as e:
        logger.error(f"[ZARA] Failed to add product '{name}' from {url}: {str(e)}")
        screenshot_path = os.path.join(os.getcwd(), f"{name.replace(' ', '_')}_error.png")
        driver.save_screenshot(screenshot_path)
        logger.error(f"[ZARA] Screenshot saved to: {screenshot_path}")
        return False
