import os
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dynamic_selector import find_best_button_xpath

logger = logging.getLogger(__name__)

def dismiss_overlays(driver):
    """
    Attempts to dismiss common overlays (cookie consent, modals, etc.) that may block the add-to-cart button.
    You may need to adjust the selectors based on observed behavior on different sites.
    """
    dismissed = False
    # List of candidate selectors that may represent an overlay's close/dismiss button.
    candidate_selectors = [
        "button[aria-label*='cookie']",          # Buttons mentioning cookie
        "button[aria-label*='accept']",          # Accept cookie or consent buttons
        "button[aria-label*='close']",           # Any close button
        "button.modal-close",                    # Example class-based selector
        "button#close-dialog",                   # Example ID-based selector
        "div.modal > button",                    # Button inside a modal container
    ]
    for selector in candidate_selectors:
        try:
            # Wait a short time for the overlay to appear and be clickable
            close_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            close_btn.click()
            logger.info(f"[GENERIC] Dismissed overlay using selector: {selector}")
            dismissed = True
            # Give the page a moment to update
            time.sleep(1)
        except Exception:
            continue
    return dismissed

def add_to_cart(driver, product, central_config=None):
    """
    Generic handler that uses dynamic selector matching to find the add-to-cart button.
    It first attempts to dismiss common overlays. Then it finds a candidate button using
    fuzzy matching based on a set of keywords.
    
    :param driver: Selenium WebDriver instance.
    :param product: Dictionary with keys 'name', 'url', optionally 'variant'
    :param central_config: (Optional) Central configuration dictionary (unused in generic handler)
    :return: True if product is successfully added, else False.
    """
    url = product["url"]
    name = product.get("name", "Unknown Product")
    variant = product.get("variant")
    
    try:
        logger.info(f"[GENERIC] Processing product: {name} ({url})")
        driver.get(url)
        time.sleep(3)  # Allow the page to load
        
        # Attempt to dismiss any overlays (cookie consent, modals, etc.)
        dismiss_overlays(driver)
        
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
                logger.info(f"[GENERIC] Selected variant '{variant}' using radio input")
                variant_found = True
                time.sleep(2)
            except Exception:
                logger.info(f"[GENERIC] Could not find radio input for variant '{variant}'")
            
            # Method 2: Try to find a button with matching text
            if not variant_found:
                try:
                    variant_xpath = f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{variant.lower()}')]"
                    variant_element = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, variant_xpath))
                    )
                    variant_element.click()
                    logger.info(f"[GENERIC] Selected variant '{variant}' using button text")
                    variant_found = True
                    time.sleep(2)
                except Exception:
                    logger.info(f"[GENERIC] Could not find button for variant '{variant}'")
            
            # Method 3: Try to find a div with matching text
            if not variant_found:
                try:
                    variant_div = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, f"//div[contains(text(), '{variant}')]"))
                    )
                    variant_div.click()
                    logger.info(f"[GENERIC] Selected variant '{variant}' using div text")
                    variant_found = True
                    time.sleep(2)
                except Exception:
                    logger.info(f"[GENERIC] Could not find div for variant '{variant}'")
            
            if not variant_found:
                logger.error(f"[GENERIC] Could not find variant '{variant}' using any method")
                return False
        
        # Wait for and click the "Add to Cart" button
        candidate_keywords = [
            "add to cart", "add to bag", "buy now", "purchase", "shop now", 
            "add product", "cart", "add item", "order now", "add", "add to shopping bag"
        ]
        xpath, button, score = find_best_button_xpath(driver, candidate_keywords)
        if xpath:
            logger.info(f"[GENERIC] Found candidate button with XPath: {xpath} (score: {score})")
            try:
                button.click()
            except Exception as click_err:
                logger.warning(f"[GENERIC] Normal click failed, attempting JavaScript click. Error: {click_err}")
                driver.execute_script("arguments[0].click();", button)
        else:
            logger.error("[GENERIC] Could not locate a candidate add-to-cart button dynamically.")
            return False

        # Optional: Add a verification step here (e.g., check cart count or confirmation message)
        time.sleep(2)
        logger.info("[GENERIC] Assuming add-to-cart was successful (verification can be added here).")
        return True

    except Exception as e:
        logger.error(f"[GENERIC] Failed to add product {name}: {e}")
        return False
