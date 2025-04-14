import difflib
import logging
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)

def find_best_button_xpath(driver, keywords, threshold=0.5):
    """
    Finds the best candidate button element whose text matches one of the keywords.
    Returns a tuple (xpath, best_element, best_score) if found, else (None, None, 0).
    """
    buttons = driver.find_elements(By.TAG_NAME, "button")
    best_score = 0.0
    best_button = None

    for btn in buttons:
        text = btn.text.lower().strip()
        if not text:
            continue
        for kw in keywords:
            ratio = difflib.SequenceMatcher(None, text, kw.lower()).ratio()
            logger.debug(f"Comparing button text '{text}' with keyword '{kw}' => ratio: {ratio}")
            if ratio > best_score:
                best_score = ratio
                best_button = btn

    if best_button is not None and best_score >= threshold:
        js_function = """
        function getElementXPath(elt) {
            var path = "";
            for (; elt && elt.nodeType === Node.ELEMENT_NODE; elt = elt.parentNode) {
                var idx = 1;
                for (var sib = elt.previousSibling; sib; sib = sib.previousSibling) {
                    if (sib.nodeType === Node.ELEMENT_NODE && sib.nodeName === elt.nodeName) {
                        idx++;
                    }
                }
                var xname = elt.nodeName.toLowerCase();
                if (idx > 1) xname += '[' + idx + ']';
                path = '/' + xname + path;
            }
            return path;
        }
        return getElementXPath(arguments[0]);
        """
        xpath = driver.execute_script(js_function, best_button)
        logger.info(f"Dynamic selector chose button with XPath: {xpath} (score: {best_score})")
        return xpath, best_button, best_score
    else:
        logger.info(f"No candidate button found. Best score: {best_score}")
        return None, None, best_score

def find_best_size_xpath(driver, variant, threshold=0.5):
    """
    Dynamically locate the best candidate size button that matches the given variant text.
    Returns a tuple (xpath, best_element, best_score) if found, else (None, None, 0).
    
    This function iterates over candidate size button elements (assumed to be <button> tags)
    and compares their text against the desired variant using fuzzy matching.
    """
    size_buttons = driver.find_elements(By.TAG_NAME, "button")
    best_score = 0.0
    best_button = None

    for btn in size_buttons:
        text = btn.text.lower().strip()
        if not text:
            continue
        ratio = difflib.SequenceMatcher(None, text, variant.lower()).ratio()
        logger.debug(f"Comparing size button text '{text}' with variant '{variant}' => ratio: {ratio}")
        if ratio > best_score:
            best_score = ratio
            best_button = btn

    if best_button is not None and best_score >= threshold:
        js_function = """
        function getElementXPath(elt) {
            var path = "";
            for (; elt && elt.nodeType === Node.ELEMENT_NODE; elt = elt.parentNode) {
                var idx = 1;
                for (var sib = elt.previousSibling; sib; sib = sib.previousSibling) {
                    if (sib.nodeType === Node.ELEMENT_NODE && sib.nodeName === elt.nodeName) {
                        idx++;
                    }
                }
                var xname = elt.nodeName.toLowerCase();
                if (idx > 1) xname += '[' + idx + ']';
                path = '/' + xname + path;
            }
            return path;
        }
        return getElementXPath(arguments[0]);
        """
        xpath = driver.execute_script(js_function, best_button)
        logger.info(f"Dynamic size selector chose button with XPath: {xpath} (score: {best_score})")
        return xpath, best_button, best_score
    else:
        logger.info(f"Could not find a good size button for variant '{variant}'. Best score: {best_score}")
        return None, None, best_score
