__author__ = 'Nathalie'

import credentials
from add_selected_to_basket import add_selected
import sys, time, re
from datetime import datetime, date, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup


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

	price = norm(price)
	offer = offer.lower()
	if re.search('any (\d) for (\d)', offer):
		result = re.search('any (\d) for (\d)', offer)
		q1, q2 = float(result.group(1)), float(result.group(2))
		discount = 1 - q2 / q1
		new_price = discount * price
		return discount, new_price
	elif 'for' in offer:
		result = re.search('(\d+) for £?(\d+(\.\d+|p)?)', offer)
		if result:
			quantity = int(result.group(1))
			total_price = result.group(2)
			price_per_item = norm(total_price) / quantity
			return round(1 - price_per_item / price, 2), price_per_item
	elif re.search('buy (\d) get (\d) free', offer):
		result = re.search('buy (\d) get (\d) free', offer)
		q1, q2 = float(result.group(1)), float(result.group(2))
		discount = 1 - q1/(q1 + q2)
		return discount, discount * price
	elif re.search('was.*now', offer):
		old_price = norm(re.search('was £?(\d+(\.\d+|p)?)', offer).group(1))
		new_price = norm(re.search('now £?(\d+(\.\d+|p)?)', offer).group(1))
		return round(1 - new_price / old_price, 2), price
	return None, price


def scrap(argv=None):
	date_format = '%d/%m/%Y'
	if argv and len(argv) > 1:
		try:
			start_date = datetime.strptime(argv[1], date_format).date()
		except:
			pass
	if len(argv) <= 1 or not start_date:
			start_date = date.today() - timedelta(days=5)
	ending_soon_date = date.today() + timedelta(days=7)

	try:
		driver = webdriver.Firefox()
		driver.get(login_url)
		login_input = driver.find_element(By.ID, 'username')
		login_input.send_keys(account)
		login_passw = driver.find_element(By.ID, 'password')
		login_passw.send_keys(passw)
		login_passw.send_keys(Keys.ENTER)
		time.sleep(3)

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
					offer_start_date = datetime.strptime(re.match('(\d{2}/\d{2}/\d{4})',
																offer_dates_str).group(1), date_format).date()
					offer_end_date = datetime.strptime(re.search('until (\d{2}/\d{2}/\d{4})',
																offer_dates_str).group(1), date_format).date()
					price_str = item.find_next(attrs={"class": "value"}).contents[0]
					discount, _ = calculate_disc(offer.contents[0], price_str)
					item_code = re.search('/(\d+)$', item['href']).group(1)
					if item_code:
						result[item_code] = (item.contents[0], offer.contents[0],
										offer_dates_str, price_str, str(discount), offer_start_date, offer_end_date)
			next_page += 1
		driver.quit()

		result = sorted(result.items(), key=lambda x: x[1][4], reverse=True)
		filename_prefix = 'offers' + time.strftime("%y%m%d")
		all_suffix = '_all'
		new_suffix = '_after_' + start_date.strftime("%m%d")
		ending_suffix = '_ending'

		def offer_to_str(item):
			return item[1][4] + " ::: " + item[1][1] + " ::: " + item[1][3] + " ::: " + \
					item[1][2] + " ::: " + item[1][0] + " ::: " + item[0] + '\n'

		with open(filename_prefix + all_suffix + '.csv', 'w', encoding="utf8") as f:
			for item in result:
				f.write(offer_to_str(item))

		with open(filename_prefix + new_suffix + '.csv', 'w', encoding="utf8") as f:
			for item in filter(lambda x: x[1][5] >= start_date, result):
				f.write(offer_to_str(item))

		with open(filename_prefix + ending_suffix + '.csv', 'w', encoding="utf8") as f:
			for item in filter(lambda x: x[1][6] <= ending_soon_date, result):
				f.write(offer_to_str(item))

		with open(filename_prefix + new_suffix + '_or_' + ending_suffix + '.csv', 'w', encoding="utf8") as f:
			for item in filter(lambda x: x[1][5] >= start_date or x[1][6] <= ending_soon_date, result):
				f.write(offer_to_str(item))

	except:
		if driver:
			driver.quit()
		return sys.exc_info()

if __name__ == '__main__':
	sys.exit(scrap(sys.argv))
