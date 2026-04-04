from __future__ import annotations

import base64
from pathlib import Path
from typing import Callable, TypeVar

import undetected_chromedriver as uc
from xvfbwrapper import Xvfb

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.print_page_options import PrintOptions
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait as WDWait

# Drivers alternativos em https://sites.google.com/chromium.org/driver/
# Instalados com snap install chromium no ubuntu (chromium é só via snap agora)
DEFAULT_DRIVER_PATH = "/usr/bin/chromedriver"
SNAP_DRIVER_PATH = "/snap/bin/chromium.chromedriver"
DEFAULT_BIN_PATH = "/usr/bin/chromium-browser"
SNAP_BIN_PATH = "/snap/bin/chromium"

T = TypeVar("T")


def remove_tags(text: str):
    while True:
        index_tag_start = text.find("<")
        index_tag_end = text.find(">", index_tag_start)
        if index_tag_start == -1 or index_tag_end == -1:
            break
        text = text[:index_tag_start] + text[index_tag_end + 1 :]
    return text


def wait_for(
    parent: SeleniumElement | SeleniumDriver, selector: str, by: str = By.CSS_SELECTOR, timeout: int = 10
) -> list[SeleniumElement]:
    driver = parent.driver if isinstance(parent, SeleniumElement) else parent
    try:
        def search():
            if isinstance(parent, SeleniumElement):
                found_elems = parent.webelement.find_elements(by, selector)
            else:
                found_elems = parent.driver.find_elements(by, selector)
            driver.logfunc(f"Found {len(found_elems)} searching for {selector}")
            return [SeleniumElement(e, driver) for e in found_elems]

        return WDWait(driver.driver, poll_frequency=1, timeout=timeout).until(lambda _: search())
    except TimeoutException:
        driver.logfunc("Timeout reached while searching for " + selector)
        return []


class SeleniumElement:
    def __init__(self, webelement: WebElement, driver: SeleniumDriver):
        self.webelement = webelement
        self.driver = driver

    def child_by_css(self, css_selector: str, timeout: int = 10) -> SeleniumElement:
        found = self.find_child_by_css(css_selector, timeout=timeout)
        if not found:
            raise NoSuchElementException(f"Cannot find child with selector {css_selector}")
        return found

    def child_by_xpath(self, xpath: str, timeout: int = 10) -> SeleniumElement:
        found = self.find_child_by_xpath(xpath, timeout=timeout)
        if not found:
            raise NoSuchElementException(f"Cannot find child with selector {xpath}")
        return found

    def find_child_by_css(self, css_selector: str, timeout: int = 10) -> SeleniumElement | None:
        found = self.all_children_by_css(css_selector, timeout=timeout)
        assert len(found) <= 1, f"Found {len(found)} children searching for {css_selector}"
        return found[0] if found else None

    def find_child_by_xpath(self, xpath: str, timeout: int = 10) -> SeleniumElement | None:
        found = self.all_children_by_xpath(xpath, timeout=timeout)
        assert len(found) <= 1, f"Found {len(found)} children searching for {xpath}"
        return found[0] if found else None

    def all_children_by_css(self, css_selector: str, timeout: int = 10) -> list[SeleniumElement]:
        return wait_for(parent=self, selector=css_selector, timeout=timeout)

    def all_children_by_xpath(self, xpath: str, timeout: int = 10) -> list[SeleniumElement]:
        return wait_for(parent=self, selector=xpath, by=By.XPATH, timeout=timeout)

    def child_by_id(self, id: str, timeout: int = 10) -> SeleniumElement:
        css_selector = f'[id="{id}"]'
        return self.child_by_css(css_selector, timeout=timeout)

    def find_child_by_id(self, id: str, timeout: int = 10) -> SeleniumElement | None:
        css_selector = f'[id="{id}"]'
        return self.find_child_by_css(css_selector, timeout=timeout)

    def all_children_by_id(self, id: str, timeout: int = 10) -> list[SeleniumElement]:
        css_selector = f'[id="{id}"]'
        return self.all_children_by_css(css_selector, timeout=timeout)

    def child_by_name(self, name: str, timeout: int = 10) -> SeleniumElement:
        css_selector = f'[name="{name}"]'
        return self.child_by_css(css_selector, timeout=timeout)

    def find_child_by_name(self, name: str, timeout: int = 10) -> SeleniumElement | None:
        css_selector = f'[name="{name}"]'
        return self.find_child_by_css(css_selector, timeout=timeout)

    def all_children_by_name(self, name: str, timeout: int = 10) -> list[SeleniumElement]:
        css_selector = f'[name="{name}"]'
        return self.all_children_by_css(css_selector, timeout=timeout)

    def child_by_tag(self, tag_name: str, timeout: int = 10) -> SeleniumElement:
        css_selector = tag_name
        return self.child_by_css(css_selector, timeout=timeout)

    def find_child_by_tag(self, tag_name: str, timeout: int = 10) -> SeleniumElement | None:
        css_selector = tag_name
        return self.find_child_by_css(css_selector, timeout=timeout)

    def all_children_by_tag(self, tag_name: str, timeout: int = 10) -> list[SeleniumElement]:
        css_selector = tag_name
        return self.all_children_by_css(css_selector, timeout=timeout)

    # XPATH METHODS ARE NOT CONVERTED TO CSS SELECTORS AND DON'T SUPPORT TIMEOUTS.
    # def child_by_xpath(self, xpath: str) -> SeleniumElement:
    #     return SeleniumElement(self.webelement.find_element(By.XPATH, xpath), self.driver)

    # def find_child_by_xpath(self, xpath: str) -> SeleniumElement | None:
    #     try:
    #         return self.child_by_xpath(xpath)
    #     except NoSuchElementException:
    #         return None

    # def all_children_by_xpath(self, xpath: str) -> List[SeleniumElement]:
    #     return [SeleniumElement(e, self.driver) for e in self.webelement.find_elements(By.XPATH, xpath)]

    def text(self) -> str:
        text = self.webelement.get_attribute("innerHTML") or ""
        return remove_tags(text).strip()

    def attr(self, attribute_name: str) -> str | None:
        return self.webelement.get_attribute(attribute_name)

    def click(self):
        self.webelement.click()

    def send_keys(self, keys: str):
        self.webelement.send_keys(keys)

    def __str__(self) -> str:
        id = self.attr("id")
        tag = self.webelement.tag_name
        return f"{tag}#{id if id else '-'}"

    def __repr__(self) -> str:
        return str(self)


class SeleniumDriver:
    def __init__(
        self,
        driver_path: str | None = None,
        logfunc: Callable[[str], None] = print,
        options: uc.ChromeOptions | None = None,
        download_path: str | None = None
    ):

        self.xvfb = Xvfb(width=1920, height=1080, colordepth=24)
        self.xvfb.start()

        """IF NO DRIVER PATH IS SPECIFIED, CHROMEDRIVERMANAGER IS USED"""

        if not options:
            options = self.build_default_options()

        if driver_path:
            self.driver = uc.Chrome(options=options, driver_executable_path=driver_path)
        else:
            self.driver = uc.Chrome(options=options)

        self.logfunc = logfunc
        self.logfunc("Starting Selenium driver")

        if download_path:
            self.driver.execute_cdp_cmd(
                "Page.setDownloadBehavior",
                {
                    "behavior": "allow",
                    "downloadPath": download_path
                }
            )

         # if (prefs := options.experimental_options.get('prefs')) and 'download.default_directory' in prefs:
         #     self.driver.execute_cdp_cmd(
         #         "Page.setDownloadBehavior",
         #         {"behavior": "allow", "downloadPath": prefs['download.default_directory']}
         #     )

        self.logfunc("Selenium driver loaded")

        # if bin_path:
        #     options.binary_location = bin_path
        # if user_data_dir := environ.get("USER_DATA_DIR"):
        #     logfunc(f"Using user data dir for chromium: {user_data_dir}")
        #     options.add_argument(f"--user-data-dir={user_data_dir}")

        # service = None
        # if not driver_path:
        #     logfunc("No driver specified. Using ChromeDriverManager...")
        #     from webdriver_manager.chrome import ChromeDriverManager

        #     service = Service(ChromeDriverManager().install())
        # else:
        #     logfunc(f"Using driver path: {driver_path}")
        #     service = Service(
        #         executable_path=driver_path, service_args=["--verbose", "--log-path=/tmp/chromedriver.log"]
        #     )
        # self.driver = webdriver.Chrome(service=service, options=options)


    @staticmethod
    def build_default_options() -> uc.ChromeOptions:
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--ignore-certificate-errors")
        # options.add_argument("--headless=new")
        # options.add_argument("--disable-gpu")
        # USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        # options.add_argument(f"user-agent={USER_AGENT}")
        options.add_argument("--disable-crash-reporter")
        options.add_argument("--kiosk-printing")
        return options


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            self.quit()
        self.xvfb.stop()

    def quit(self):
        self.logfunc("Closing browser driver")
        self.driver.quit()

    def get(self, url: str, timeout=300):
        self.driver.set_page_load_timeout(timeout)
        self.logfunc("Retrieving " + url)
        self.driver.get(url)

    def by_css(self, css_selector: str, timeout: int = 10) -> SeleniumElement:
        found = self.find_by_css(css_selector, timeout=timeout)
        if not found:
            raise NoSuchElementException(f"Cannot find element with selector {css_selector}")
        return found

    def by_xpath(self, xpath: str, timeout: int = 10) -> SeleniumElement:
        found = self.find_by_xpath(xpath, timeout=timeout)
        if not found:
            raise NoSuchElementException(f"Cannot find element with selector {xpath}")
        return found

    def find_by_css(self, css_selector: str, timeout: int = 10) -> SeleniumElement | None:
        found = self.all_by_css(css_selector, timeout=timeout)
        assert len(found) <= 1, f"Found {len(found)} elements searching for {css_selector}"
        return found[0] if found else None

    def find_by_xpath(self, xpath: str, timeout: int = 10) -> SeleniumElement | None:
        found = self.all_by_xpath(xpath, timeout=timeout)
        assert len(found) <= 1, f"Found {len(found)} elements searching for {xpath}"
        return found[0] if found else None

    def all_by_css(self, css_selector: str, timeout: int = 10) -> list[SeleniumElement]:
        return wait_for(parent=self, selector=css_selector, timeout=timeout)

    def all_by_xpath(self, xpath: str, timeout: int = 10) -> list[SeleniumElement]:
        return wait_for(parent=self, selector=xpath, by=By.XPATH, timeout=timeout)

    def by_id(self, id: str, timeout: int = 10) -> SeleniumElement:
        css_selector = f'[id="{id}"]'
        return self.by_css(css_selector, timeout=timeout)

    def find_by_id(self, id: str, timeout: int = 10) -> SeleniumElement | None:
        css_selector = f'[id="{id}"]'
        return self.find_by_css(css_selector, timeout=timeout)

    def all_by_id(self, id: str, timeout: int = 10) -> list[SeleniumElement]:
        css_selector = f'[id="{id}"]'
        return self.all_by_css(css_selector, timeout=timeout)

    def by_name(self, name: str, timeout: int = 10) -> SeleniumElement:
        css_selector = f'[name="{name}"]'
        return self.by_css(css_selector, timeout=timeout)

    def find_by_name(self, name: str, timeout: int = 10) -> SeleniumElement | None:
        css_selector = f'[name="{name}"]'
        return self.find_by_css(css_selector, timeout=timeout)

    def all_by_name(self, name: str, timeout: int = 10) -> list[SeleniumElement]:
        css_selector = f'[name="{name}"]'
        return self.all_by_css(css_selector, timeout=timeout)

    def by_tag(self, tag_name: str, timeout: int = 10) -> SeleniumElement:
        css_selector = tag_name
        return self.by_css(css_selector, timeout=timeout)

    def find_by_tag(self, tag_name: str, timeout: int = 10) -> SeleniumElement | None:
        css_selector = tag_name
        return self.find_by_css(css_selector, timeout=timeout)

    def all_by_tag(self, tag_name: str, timeout: int = 10) -> list[SeleniumElement]:
        css_selector = tag_name
        return self.all_by_css(css_selector, timeout=timeout)

    # XPATH METHODS ARE NOT CONVERTED TO CSS SELECTORS AND DON'T SUPPORT TIMEOUTS.
    # def by_xpath(self, xpath: str) -> SeleniumElement:
    #     return SeleniumElement(self.driver.find_element(By.XPATH, xpath), self)

    # def find_by_xpath(self, xpath: str) -> SeleniumElement | None:
    #     try:
    #         return self.by_xpath(xpath)
    #     except NoSuchElementException:
    #         return None

    # def all_by_xpath(self, xpath: str) -> List[SeleniumElement]:
    #     return [SeleniumElement(e, self) for e in self.driver.find_elements(By.XPATH, xpath)]

    def print_page(self, path: Path | str, width: float, height: float):
        """Saves a page as PDF in the given path.
        A3 = 29.7 x 42; A4 = 21 x 29.7
        """
        print_options = PrintOptions()
        print_options.page_width = width
        print_options.page_height = height
        # print_options.margin_left = 1.0
        # print_options.margin_right = 1.0
        pdf_data = self.driver.print_page(print_options=print_options)
        with open(path, "wb") as f:
            f.write(base64.b64decode(pdf_data))

    def print_page_source(self, path: str | None = None) -> str:
        if path:
            with open(path, "w") as f:
                f.write(self.driver.page_source)
        return self.driver.page_source
