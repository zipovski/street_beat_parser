from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import selenium.common.exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from time import sleep
from selenium.webdriver import ActionChains 
from bs4 import BeautifulSoup 
import random
import pandas as pd
import re
import warnings
from datetime import datetime
import sys
warnings.filterwarnings("ignore")

def selenium_config() -> webdriver:

    #regualar driver settings
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    #execute script on every page load (Chrome Devtools Protocol)
    #deleting webdriver detection variable
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source":
            "const newProto = navigator.__proto__;"
            "delete newProto.webdriver;"
            "navigator.__proto__ = newProto;"
        })
    
    return driver

def get_window(source: str, driver: webdriver) -> None:

    driver.get(source)
    sleep(3)
    #close region choice window if exists
    try:
        driver.find_element(by = By.XPATH, value = '/html/body/div[4]/div/div[1]/header/button').click()
    except selenium.common.exceptions.NoSuchElementException:
        pass
    sleep(1)

def whole_page_load(driver) -> str:

    scroll_bottom = "window.scrollTo(0, document.body.scrollHeight - document.body.scrollHeight*0.2)"
    scroll_top = "window.scrollTo(0, 0)"

    #load the whole page via "show more" button if exists
    #if not, scroll to the top and return page source
    for i in range(100):
        try:
            driver.execute_script(scroll_bottom)
            sleep(0.5)
            driver.find_element(by = By.XPATH, value = '/html/body/div[3]/div/div[5]/button').click()
            sleep(random.randint(2, 3))
        except selenium.common.exceptions.NoSuchElementException:
            driver.execute_script(scroll_top)
            sleep(3)
            break
    
    return driver.page_source

def get_products(driver: webdriver) -> list:

    bs = whole_page_load(driver)
    source = BeautifulSoup(bs, "lxml")
    #find all product links
    prods = source.find_all("div", {"class" : "product-card product-card--hoverable"})
    prod_links = [prod.find("a")["href"] for prod in prods]
    prod_links = ["https://street-beat.ru" + prod for prod in prod_links]

    return prod_links

def get_prod_info(source: BeautifulSoup, url: str) -> dict:
    
    try:
        id = source.find("div", {"class" : "product-specs__article"}).text
        id = id.replace("Арт.", "")
        id = re.sub("\s+", " ", id)
    except Exception as e:
        id = None

    try:
        name = source.find("h1", {"class" : "product-specs__title h1"}).text
        name = re.sub("\s+", " ", name)
        name.strip()
        name = name.replace("\xa0", " ")
    except Exception as e:
        name = None

    try:
        price = source.find("span", {"class" : "price-tag__default"}).text
        price = price.replace("руб.", "")
        price = re.sub("\s+", " ", price)
        price = price.strip()
        price = int(price.replace(" ", ""))
    except Exception as e:
        price = None

    try: 
        brand = source.find("div", {"class" : "tags-list"})
        brand = brand.find_all("a")[2].text
        brand = brand.replace("Другие товары", "")
        brand = re.sub("\s+", " ", brand)
        brand = brand.strip()
    except Exception as e:
        brand = None

    try:
        sizes = source.find("div", {"class" : "sizes-list"})
        sizes = len(sizes.find_all("button", {"class" : "sizes-list__item"}))
    except Exception as e:
        sizes = None

    try:
        country = source.find("div", {"class" : "v-html-list"}).text
        country = country.split("Страна производства: ")[1]
        country = re.sub("\s+", " ", country)
        country = country.strip()
    except Exception as e:
        country = None

    try:
        features = source.find_all("div", {"class" : "features__item"})
        for element in features:
            if "Состав" in element.text:
                material = element.text
                material = material.replace("Состав", "")
        material = re.sub("\s+", " ", material)
        material = material.strip()
    except Exception as e:
        material = None

    if name == None:
        print("Unexpected error in", url)

    return {"ID" : id, "Name" : name, "Price" : price,  "Brand" : brand, 
            "Sizes_amount" : sizes, "Country" : country, "Material" : material, "URL" : url}

def download_info(source: list, driver: webdriver) -> pd.DataFrame:
    
    #remove duplicates from list
    source = list(set(source))

    #initial df
    df = pd.DataFrame(columns = ["ID", "Name", "Price", "Brand", 
                                "Sizes_amount", "Country", "Material"])

    for element in source:
        driver.get(element)
        sleep(1)
        bs = BeautifulSoup(driver.page_source, "lxml")
        info = get_prod_info(bs, element)
        df = df.append(info, ignore_index = True)
        print(f'{source.index(element) + 1}/{len(source)} downloaded')
    
    return df

def df_formatting(df: pd.DataFrame) -> None:

    cur_time = datetime.now()
    cur_time = cur_time.strftime("%d_%m_%Y_%H_%M")

    df.drop_duplicates(keep = "first", inplace = True)
    df.to_csv(f'./results_{cur_time}.csv', sep = "\t", encoding = "utf-8")


def main():

    if len(sys.argv) == 1:
        target_url = "https://street-beat.ru/cat"
    else:
        sys.argv.pop(0)
        argument = "%20".join(sys.argv)
        target_url = f'https://street-beat.ru/cat/?q={argument}'

    driver = selenium_config()
    get_window(source = target_url, driver = driver)
    prods = get_products(driver = driver)
    prod_dataframe = download_info(prods, driver = driver)
    df_formatting(prod_dataframe)
    driver.quit()

if __name__ == "__main__":
    main()
