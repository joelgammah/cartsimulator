# brands/hm_handler.py
import json
import os
import time
import logging
import re
import traceback
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

logger = logging.getLogger(__name__)

# Load the central configuration from the project root.
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
with open(CONFIG_PATH, "r") as f:
    CONFIG = json.load(f)

def get_hm_config():
    """
    Returns H&M-specific configuration if available, otherwise falls back to default.
    """
    return CONFIG.get("h&m", CONFIG["default"])

def add_to_cart(driver, product, central_config=None):
    """
    Adds an H&M product to the shopping bag.
    
    :param driver: Selenium webdriver instance.
    :param product: Dictionary with keys "name", "url", and optional "variant"
    :return: True if addition succeeded, False otherwise.
    """
    url = product["url"]
    name = product["name"]
    variant = product.get("variant")
    
    config = get_hm_config()
    timeouts = config.get("timeouts", {})
    timeout_default = timeouts.get("default", 10)
    timeout_variant = timeouts.get("variant", 10)
    
    try:
        logger.info(f"[H&M] Processing product: {name} ({url})")
        driver.get(url)
        
        # If variant is specified, first click the size button.
        if variant:
            # Try different size button indices
            size_found = False
            for index in range(0, 10):  # Try indices 1-9
                try:
                    size_option_xpath = config["size_option_xpath_template"].replace("{index}", str(index)).replace("{variant}", variant)
                    size_option = WebDriverWait(driver, 2).until(  # Shorter timeout for each attempt
                        EC.element_to_be_clickable((By.XPATH, size_option_xpath))
                    )
                    size_option.click()
                    logger.info(f"[H&M] Selected size '{variant}' for: {name}")
                    size_found = True
                    break
                except:
                    continue
            
            if not size_found:
                logger.error(f"[H&M] Could not find size '{variant}' for: {name}")
                return False
        
        # Now click the "Add to Bag" button.
        add_to_bag_xpath = config["add_to_cart_button_xpath"]
        add_to_bag_button = WebDriverWait(driver, timeout_default).until(
            EC.element_to_be_clickable((By.XPATH, add_to_bag_xpath))
        )
        add_to_bag_button.click()
        logger.info(f"[H&M] Clicked Add to Bag for: {name}")
        
        # Pause for a short time for the bag to update.
        time.sleep(2)
        
        # Verify the product was added by checking the cart count element.
        cart_count_xpath = config["cart_count_xpath"]
        cart_count_element = WebDriverWait(driver, timeout_default).until(
            EC.presence_of_element_located((By.XPATH, cart_count_xpath))
        )
        cart_text = cart_count_element.text.strip()
        
        # Extract the number from text like "Shopping bag (1)"
        match = re.search(r'\((\d+)\)', cart_text)
        if match:
            cart_count = int(match.group(1))
            if cart_count > 0:
                logger.info(f"[H&M] Successfully added product; bag count: {cart_count}")
                return True
            else:
                logger.error("[H&M] Bag count did not update as expected.")
                return False
        else:
            logger.error(f"[H&M] Could not parse cart count from text: {cart_text}")
            return False

    except Exception as e:
        logger.error(f"[H&M] Failed to add product '{name}' from {url}: {str(e)}")
        return False

def process_product(driver, product):
    """Process an H&M product"""
    try:
        name = product["name"]
        url = product["url"]
        variant = product.get("variant")
        
        logger.info(f"[H&M] Processing product: {name} ({url})")
        
        # Navigate to product page
        driver.get(url)
        
        # Accept cookie consent if present
        try:
            cookie_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_button.click()
            logger.info("[H&M] Accepted cookie consent")
        except TimeoutException:
            logger.info("[H&M] No cookie consent banner found")
        
        # Handle signup popup if present
        try:
            driver.switch_to.frame("attentive_creative")
            close_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Close dialog']"))
            )
            close_button.click()
            driver.switch_to.default_content()
            logger.info("[H&M] Closed signup popup")
        except:
            logger.info("[H&M] No signup popup found")
            driver.switch_to.default_content()
        
        # Select size if specified
        if variant:
            handler = HmHandler(driver, product)
            if not handler.select_size(variant):
                return False
            if not handler.add_to_cart():
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"[H&M] Failed to add product '{name}' from {url}: {str(e)}")
        traceback.print_exc()
        return False

class HmHandler:
    def __init__(self, driver, product):
        self.driver = driver
        self.product = product
        self.product_name = product["name"]
        self.product_url = product["url"]
        self.product_variant = product.get("variant")

    def handle_popups(self):
        """Handle any popups or overlays that might interfere with interactions"""
        try:
            # Handle Attentive popup
            attentive_frame = self.driver.find_element(By.ID, "attentive_creative")
            if attentive_frame:
                print("[H&M] Found Attentive popup, attempting to close...")
                self.driver.switch_to.frame(attentive_frame)
                close_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Close dialog']")
                if close_button:
                    close_button.click()
                self.driver.switch_to.default_content()
                print("[H&M] Closed Attentive popup")
        except:
            pass

        try:
            # Handle newsletter signup
            newsletter_close = self.driver.find_element(By.CSS_SELECTOR, "button.close-button")
            if newsletter_close:
                newsletter_close.click()
                print("[H&M] Closed newsletter popup")
        except:
            pass

    def select_size(self, size):
        """Select size for the product."""
        try:
            # Wait for size list to be present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid^='sizeButton-']"))
            )

            # First try to find size button by exact data-testid and aria-label match
            try:
                size_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f'[data-testid^="sizeButton-"][aria-label="{size} null"]'))
                )
                size_button.click()
                logger.info(f"[H&M] Selected size '{size}' using exact data-testid and aria-label match")
                return True
            except TimeoutException:
                logger.info(f"[H&M] Could not find exact match for size '{size}'")

            # Try to find the input element with the exact size ID
            try:
                size_input = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, f'input[id="{size}"]'))
                )
                parent_div = size_input.find_element(By.XPATH, "./..")
                self.driver.execute_script("arguments[0].click();", parent_div)
                logger.info(f"[H&M] Selected size '{size}' using input ID")
                return True
            except TimeoutException:
                logger.info(f"[H&M] Could not find input element for size '{size}'")

            # Try to find the label element with exact size text
            try:
                size_label = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, f"//label[normalize-space(text())='{size}']"))
                )
                size_label.click()
                logger.info(f"[H&M] Selected size '{size}' using label text")
                return True
            except TimeoutException:
                logger.info(f"[H&M] Could not find label element for size '{size}'")

            logger.error(f"[H&M] Could not find size '{size}' using any method")
            return False
        except Exception as e:
            logger.error(f"[H&M] Error selecting size: {str(e)}")
            return False

    def add_to_cart(self):
        """Add the product to cart"""
        try:
            # Handle any popups before proceeding
            self.handle_popups()
            
            # Find and click the Add to Bag button
            add_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='pdp_add_to_cart_button']"))
            )
            
            try:
                add_button.click()
            except:
                self.driver.execute_script("arguments[0].click();", add_button)
            
            print(f"[H&M] Clicked Add to Bag for: {self.product_name}")
            
            # Wait for the bag count to update
            time.sleep(2)
            
            # Get the updated bag count
            bag_text = self.driver.find_element(By.XPATH, "//span[contains(@class, 'd86975') and contains(text(), 'Shopping bag')]").text
            count = int(''.join(filter(str.isdigit, bag_text)))
            print(f"[H&M] Successfully added product; bag count: {count}")
            return True
        except Exception as e:
            print(f"[H&M] Error adding to cart: {str(e)}")
            traceback.print_exc()
            return False
