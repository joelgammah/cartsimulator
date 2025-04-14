# brands/nike_handler.py
import os
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dynamic_selector import find_best_button_xpath  # For add-to-cart button dynamic selection

logger = logging.getLogger(__name__)

def get_nike_config(central_config):
    """
    Returns Nike-specific configuration from the central configuration.
    Falls back to the default if Nike-specific settings are missing.
    """
    return central_config.get("nike", central_config["default"])

def dismiss_overlays(driver):
    """
    Attempts to dismiss any overlays that might interfere with clicking the add to cart button.
    """
    try:
        # Try to find and close any modal overlays
        overlays = driver.find_elements(By.CSS_SELECTOR, "div[class*='Modal'], div[class*='modal'], div[class*='overlay']")
        for overlay in overlays:
            try:
                close_button = overlay.find_element(By.CSS_SELECTOR, "button[aria-label*='Close'], button[class*='close']")
                close_button.click()
                logger.info("[NIKE] Closed an overlay")
                time.sleep(1)
            except:
                # If we can't find a close button, try to remove the overlay using JavaScript
                driver.execute_script("arguments[0].remove();", overlay)
                logger.info("[NIKE] Removed an overlay using JavaScript")
                time.sleep(1)
    except Exception as e:
        logger.warning(f"[NIKE] Error while trying to dismiss overlays: {e}")

def add_to_cart(driver, product, central_config=None):
    """
    Adds a Nike product to the shopping cart using dynamic selectors.
    
    :param driver: Selenium WebDriver instance.
    :param product: Dictionary with keys 'name', 'url', optionally 'variant'
    :param central_config: (Optional) Central configuration dictionary
    :return: True if product is successfully added, else False.
    """
    url = product["url"]
    name = product.get("name", "Unknown Product")
    variant = product.get("variant")
    
    try:
        logger.info(f"[NIKE] Processing product: {name} ({url})")
        driver.get(url)
        time.sleep(3)  # Allow the page to load
        
        # If a variant is specified, select it first
        if variant:
            # Try different methods to find and select the variant
            variant_found = False
            
            # Method 1: Try to find a radio input with matching value
            try:
                radio_input = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, f'input[type="radio"][value="{variant}"]'))
                )
                # Click the associated label
                label = driver.find_element(By.CSS_SELECTOR, f'label[for="{radio_input.get_attribute("id")}"]')
                label.click()
                logger.info(f"[NIKE] Selected variant '{variant}' using radio input")
                variant_found = True
                time.sleep(2)  # Wait after size selection
            except Exception:
                logger.info(f"[NIKE] Could not find radio input for variant '{variant}'")
            
            # Method 2: Try to find a button with matching text
            if not variant_found:
                try:
                    variant_xpath = f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{variant.lower()}')]"
                    variant_element = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, variant_xpath))
                    )
                    variant_element.click()
                    logger.info(f"[NIKE] Selected variant '{variant}' using button text")
                    variant_found = True
                    time.sleep(2)  # Wait after size selection
                except Exception:
                    logger.info(f"[NIKE] Could not find button for variant '{variant}'")
            
            # Method 3: Try to find a div with matching text
            if not variant_found:
                try:
                    variant_div = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, f"//div[contains(text(), '{variant}')]"))
                    )
                    variant_div.click()
                    logger.info(f"[NIKE] Selected variant '{variant}' using div text")
                    variant_found = True
                    time.sleep(2)  # Wait after size selection
                except Exception:
                    logger.info(f"[NIKE] Could not find div for variant '{variant}'")
            
            if not variant_found:
                logger.error(f"[NIKE] Could not find variant '{variant}' using any method")
                return False
        
        # Wait for and click the "Add to Cart" button using dynamic selector
        candidate_keywords = [
            "add to cart", "add to bag", "buy now", "purchase", "shop now", 
            "add product", "cart", "add item", "order now", "add", "add to shopping bag"
        ]
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # First try to dismiss any overlays
                dismiss_overlays(driver)
                time.sleep(2)
                
                xpath, button, score = find_best_button_xpath(driver, candidate_keywords)
                if xpath:
                    logger.info(f"[NIKE] Found candidate button with XPath: {xpath} (score: {score})")
                    try:
                        # Scroll the button into view
                        driver.execute_script("arguments[0].scrollIntoView(true);", button)
                        time.sleep(2)
                        
                        # Try to remove any overlays again right before clicking
                        dismiss_overlays(driver)
                        time.sleep(1)
                        
                        # Try to click using different methods
                        try:
                            button.click()
                        except:
                            try:
                                driver.execute_script("arguments[0].click();", button)
                            except:
                                # If both methods fail, try to force the click by removing overlays and using JavaScript
                                driver.execute_script("""
                                    // Remove any overlays
                                    document.querySelectorAll('div[class*="Modal"], div[class*="modal"], div[class*="overlay"]').forEach(e => e.remove());
                                    // Force click the button
                                    arguments[0].click();
                                """, button)
                    
                    except Exception as click_err:
                        logger.warning(f"[NIKE] Click failed: {click_err}")
                        if attempt < max_retries - 1:
                            continue
                    
                    # Wait for any error messages
                    time.sleep(3)
                    
                    # Check for error messages
                    error_messages = driver.find_elements(By.XPATH, "//div[contains(@class, 'error') or contains(@class, 'message')]")
                    if error_messages:
                        error_text = error_messages[0].text
                        logger.warning(f"[NIKE] Error message detected: {error_text}")
                        if attempt < max_retries - 1:
                            logger.info(f"[NIKE] Retrying... Attempt {attempt + 2} of {max_retries}")
                            time.sleep(5)  # Wait before retrying
                            continue
                        else:
                            logger.error("[NIKE] Max retries reached. Could not add to cart.")
                            return False
                    
                    # If no error messages, assume success
                    logger.info("[NIKE] No error messages detected. Assuming add-to-cart was successful.")
                    return True
                else:
                    logger.error("[NIKE] Could not locate a candidate add-to-cart button dynamically.")
                    return False
            except Exception as e:
                logger.error(f"[NIKE] Error during add to cart attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                else:
                    return False

    except Exception as e:
        logger.error(f"[NIKE] Failed to add product {name}: {e}")
        return False
