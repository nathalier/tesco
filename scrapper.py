__author__ = 'Nathalie'

import sys, time, re
import credentials
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from urllib.request import urlopen


login_url = 'https://secure.tesco.com/account/en-GB/login?from=/'
fav_url = 'https://www.tesco.com/groceries/en-GB/favorites'
fav_trunc_url = '/groceries/en-GB/favorites?page='
account = credentials.account
passw = credentials.passw

def main(argv=None):
    try:
        # if argv is None:
        #     argv = sys.argv
        # import_module(argv)
        driver = webdriver.Firefox()
        driver.get(login_url)
        login_input = driver.find_element(By.ID, 'username')
        login_input.send_keys(account)
        login_passw = driver.find_element(By.ID, 'password')
        login_passw.send_keys(passw)
        login_passw.send_keys(Keys.ENTER)
        time.sleep(3)
        # close_btn = driver.find_element(By.CLASS_NAME, 'close-btn')
        # close_btn.click()

        ids_list = []
        next_page = 1
        while True:
            driver.get(fav_url + '?page=' + str(next_page))
            # time.sleep(3)
            html = driver.page_source
            soup = BeautifulSoup(html)
            product_list = soup.find('div', {"class": "results-page"})
            favs = product_list.find_all('a', {"class": "product-tile--title"})
            if len(favs) == 0:
                break
            with open('result.csv', 'a') as f:
                for a in favs:
                    f.write(a['href'] + "," + a.contents[0] + '\n')
                    ids_list.append(re.findall('\d+', a['href'])[0])
            next_page += 1

        ids = ', '.join(ids_list)
        with open('ids.txt', 'w') as f:
            f.write(ids)
    except:
        return sys.exc_info()



if __name__ == '__main__':
    sys.exit(main())
