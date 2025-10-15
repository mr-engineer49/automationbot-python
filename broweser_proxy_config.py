import json
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions


class BrowserProxyConfig:
    def __init__(self, proxy=None):
        self.driver = None
        self.proxy = proxy


    #function to load the proxies from the json 
    def load_proxifly_proxy_from_json(self):
        try:
            with open("proxies.json", "r") as f:
                proxies = json.load(f)
            proxy = random.choice(proxies)
            proxy_address = f"{proxy['ip']}:{proxy['port']}"
            proxy_full = f"{proxy['protocol']}://{proxy_address}"
            print(f" Using proxy: {proxy['protocol']}://{proxy_address} ({proxy['geolocation']['country']})")
            return proxy_full
        except Exception as e:
            print(f" Failed to load proxy: {e}")
            return None


    #browsers set up
    def browser_type_google(self):
        options = ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--headless")
        if self.proxy:
            options.add_argument(f'--proxy-server={self.proxy}')
        else:
            print(" No proxy applied.")
            options.add_argument("--proxy-server=direct://")
        self.driver = webdriver.Chrome(options=options)

    def browser_type_firefox(self):
        options = FirefoxOptions()
        options.add_argument("--start-maximized")
        if self.proxy:
            ip, port = self.proxy.split("://")[1].split(":")
            options.set_preference("network.proxy.type", 1)
            options.set_preference("network.proxy.socks", ip)
            options.set_preference("network.proxy.socks_port", int(port))
        else:
            print("No proxy applied.")
            options.set_preference("network.proxy.type", 0)
        self.driver = webdriver.Firefox(options=options)

    def browser_type_edge(self):
        options = EdgeOptions()
        options.add_argument("--start-maximized")
        if self.proxy:
            options.add_argument(f'--proxy-server={self.proxy}')
        else:
            print("🕸️ No proxy applied.")
            options.add_argument("--proxy-server=direct://")
        self.driver = webdriver.Edge(options=options)


    def open_url(self, url):
        self.driver.get(url)


    def close(self):
        self.driver.quit()

