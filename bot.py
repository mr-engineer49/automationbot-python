from asyncio import protocols
import random
import os
import time
import requests
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


#ENV
PROXYFLY_API_KEY = os.getenv('PROXYFLY_API_KEY')
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')



class AutomatedBot:
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



#main set up 
def mainConfig():
#airtable set up    
    if not AIRTABLE_API_KEY:
        print("Error: AIRTABLE_API_KEY not found in environment variables.")
        return

    print("Fetching new items from Airtable...")

    base_id = "appDsYq8b5IjHTSfP"
    table_name = "tblrBVDNH4bzoMCZQ"
    table_view_name = "Ready to Run View"

    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"

    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    params = {"view": table_view_name}

    try:
        print(" Requesting Airtable...")
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        records = data.get('records', [])

        if not records:
            print(" No records found.")
            return

        print("Airtable data received.")
        urls = []
        for record in records:
            fields = record.get('fields', {})
            title = fields.get('Campaign Name')
            link = fields.get('Affiliate URl')
            script_area = fields.get('Script Area')
            if link:
                urls.append((title, link, script_area))

        if not urls:
            print(" No URLs found.")
            return



#getting the data from the airtable
        title, random_url, script_area = random.choice(urls)
        print(f" Selected URL: {random_url} from -> {title}")




#trying to config the bot with proxy set up 
        temp_bot = AutomatedBot()
        proxy = temp_bot.load_proxifly_proxy_from_json()
        bot = AutomatedBot(proxy=proxy)
        if not proxy:
            print(" No proxies available.")
            return
        print(f" Using Proxy: {proxy}")



#exectubg the but by open the url and excecute the script        
        bot.browser_type_google()
        bot.open_url(random_url)
        print(" Bot opening URL...")
        time.sleep(30)
        print("Starting to excecute the script")
        bot.excecute(script_area)
        print("Script finished. Closing browser.")
        time.sleep(2)
        bot.close()
    except Exception as e:
        print(f" Error occurred: {e}")


if __name__ == "__main__":
    mainConfig()
