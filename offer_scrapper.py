__author__ = 'Nathalie'


import credentials
import sys, time, re
from selenium import webdriver
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

		result = {}
		next_page = 1
		while True:
			driver.get(fav_url + '?page=' + str(next_page))
			html = driver.page_source
			soup = BeautifulSoup(html)
			soup.find_all()
			product_list = soup.find('div', {"class": "results-page"})
			items = product_list.find_all('a', {"class": "product-tile--title"})
			if len(items) == 0:
				break
			for item in items:
				offer_block = item.next_sibling.find("ul", {"class": "product-promotions"})
				if offer_block:
					offer = offer_block.find(attrs={"class": "offer-text"})
					offer_dates_str = offer.next_sibling.contents[0].replace('Offer valid for delivery from ', '')
					price_str = item.find_next(attrs={"class": "value"}).contents[0]
					# if offer_dates_str.startswith('21/11') or offer_dates_str.startswith('22/11'):
					item_code = re.search('/(\d+)$', item['href']).group(1)
					if item_code:
						result[item_code] = (item.contents[0], offer.contents[0],
										offer_dates_str, price_str)
			next_page += 1
			break
		driver.quit()

		result = sorted(result.items())
		with open('offers' + time.strftime("%Y%m%d_%H%M") + '.csv', 'w', encoding="utf8") as f:
			for item in result:
				f.write(item[1][1] + " ::: " + item[1][3] + " ::: " + item[1][2] +\
						" ::: " + item[1][0] + " ::: " + item[0] + '\n')
	except:
		if driver:
			driver.quit()
		return sys.exc_info()

if __name__ == '__main__':
	sys.exit(main())
