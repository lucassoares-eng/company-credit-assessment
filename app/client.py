import os
import random
import time
from .utils import (
    initialize_driver,
    load_cookies,
    prompt_login,
    save_cookies,
    get_chrome_version,
    get_chromedriver_url,
    update_chromedriver,
)

class DriverManager:
    def __init__(self, instagram_url, cookies_file):
        self.driver = None
        self.instagram_cookies_file = cookies_file
        self.instagram_url = instagram_url
        self.chrome_version = get_chrome_version()
        update_chromedriver(get_chromedriver_url(self.chrome_version))
        self._setup_driver()

    def _setup_driver(self):
        """Initialize and set up the WebDriver."""
        self.driver = initialize_driver()
        if os.path.exists(self.instagram_cookies_file):
            while True:
                try:
                    self.driver.set_page_load_timeout(30)
                    self.driver.get(self.instagram_url)
                    break
                except Exception as e:
                    print(f"Error initializing driver: {e}")
                    self.driver.quit()
                    # Retry process from the beginning
                    return self._setup_driver(self)
            load_cookies(self.driver, self.instagram_cookies_file)
        else:
            self._prompt_login()

    def _prompt_login(self):
        """Prompt user to log in and save cookies."""
        prompt_login(self.instagram_url, self.instagram_cookies_file)

    def restart_driver(self):
        """Restart the WebDriver with a random delay."""
        if self.driver:
            self.driver.get(self.instagram_url)
            save_cookies(self.driver, self.instagram_cookies_file)
            self.driver.quit()
            random_sleep = int(random.uniform(30, 90))
            print(f"Driver stopped, waiting {random_sleep} seconds to restart...")
            time.sleep(random_sleep)
        # Reinitialize the driver
        self._setup_driver()
        print("Driver restarted successfully!")

    def get_driver(self):
        """Return the active WebDriver instance."""
        return self.driver