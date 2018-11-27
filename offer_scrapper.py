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


def calculate_disc(offer, price):
	def norm(p):
		if p[-1] == 'p':
			return float(p[:-1]) / 100
		else:
			return float(p)

	offer = offer.lower()
	if re.search('any (\d) for (\d)', offer):
		result = re.search('any (\d) for (\d)', offer)
		q1, q2 = float(result.group(1)), float(result.group(2))
		return 1 - q2 / q1
	elif 'for' in offer:
		result = re.search('(\d+) for £?(\d+(\.\d+|p))', offer)
		if result:
			quantity = int(result.group(1))
			total_price = result.group(2)
			price_per_item = norm(total_price) / quantity
			return round(1 - price_per_item / float(price), 2)
	elif re.search('buy (\d) get (\d) free', offer):
		result = re.search('buy (\d) get (\d) free', offer)
		q1, q2 = float(result.group(1)), float(result.group(2))
		return 1 - q1/(q1 + q2)
	elif re.search('was.*now', offer):
		old_price = norm(re.search('was £?(\d+(\.\d+|p))', offer).group(1))
		new_price = norm(re.search('now £?(\d+(\.\d+|p))', offer).group(1))
		return round(1 - new_price / old_price, 2)
	else:
		return

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
					discount = calculate_disc(offer.contents[0], price_str)
					item_code = re.search('/(\d+)$', item['href']).group(1)
					if item_code:
						result[item_code] = (item.contents[0], offer.contents[0],
										offer_dates_str, price_str, str(discount))
			next_page += 1
		driver.quit()

		result = sorted(result.items(), key=lambda x: x[1][4], reverse=True)
		with open('offers' + time.strftime("%Y%m%d_%H%M") + '.csv', 'w', encoding="utf8") as f:
			for item in result:
				f.write(item[1][4] + " ::: " + item[1][1] + " ::: " + item[1][3] + " ::: " +\
						item[1][2] + " ::: " + item[1][0] + " ::: " + item[0] + '\n')
	except:
		if driver:
			driver.quit()
		return sys.exc_info()

if __name__ == '__main__':
	sys.exit(main())
