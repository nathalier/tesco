__author__ = 'Nathalie'

from ignored_io import get_ignored
import credentials
from collections import namedtuple
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


def calculate_discount(offer: str, price: str):
	def norm(p):
		""" returns float value of a price in pounds"""
		if p[-1] == 'p':
			return float(p[:-1]) / 100
		elif p[0] == '£':
			return float(p[1:])
		else:
			return float(p)

	price = norm(price)
	offer = offer.lower()
	if re.search('any (\d) for (\d)', offer):
		result = re.search('any (\d) for (\d)', offer)
		q1, q2 = float(result.group(1)), float(result.group(2))
		discount = 1 - q2 / q1
		return discount, price
	elif 'for' in offer:
		result = re.search('(\d+) for £?(\d+(\.\d+|p)?)', offer)
		if result:
			quantity = int(result.group(1))
			total_price = result.group(2)
			price_per_item = norm(total_price) / quantity
			return round(1 - price_per_item / price, 2), price
	elif re.search('buy (\d) get (\d) free', offer):
		result = re.search('buy (\d) get (\d) free', offer)
		q1, q2 = float(result.group(1)), float(result.group(2))
		discount = 1 - q1/(q1 + q2)
		return discount, price
	elif re.search('was.*now', offer):
		old_price = norm(re.search('was £?(\d+(\.\d+|p)?)', offer).group(1))
		new_price = norm(re.search('now £?(\d+(\.\d+|p)?)', offer).group(1))
		return round(1 - new_price / old_price, 2), old_price
	return 0, price


def filter_out(promos):
	ignore_discount = 0.11
	ignore_offers, ignore_products, not_intr_offers = get_ignored()
	filtered = {}
	for product in promos:
		if product in ignore_products or\
				promos[product][1] in ignore_offers or \
				(product in not_intr_offers and promos[product][7] >= not_intr_offers[product]) or\
				promos[product][4] <= ignore_discount:
			continue
		filtered[product] = promos[product]
	return filtered


def scrap():
	date_format = '%d/%m/%Y'

	try:
		driver = webdriver.Firefox()
		driver.get(login_url)
		login_input = driver.find_element(By.ID, 'username')
		login_input.send_keys(account)
		login_passw = driver.find_element(By.ID, 'password')
		login_passw.send_keys(passw)
		time.sleep(1)
		login_passw.send_keys(Keys.ENTER)
		time.sleep(7)

		result = {}
		Offer = namedtuple('Offer', 'item_name, offer_name, offer_dates_str, price_str, discount, '
									'offer_start_date, offer_end_date, price_offered, item_code')
		next_page = 1
		while True:
			driver.get(fav_url + '?page=' + str(next_page))
			html = driver.page_source
			soup = BeautifulSoup(html)
			product_list = soup.find('div', {"class": "results-page"})
			items = product_list.find_all('li', {'class': 'product-list--list-item'})
			if len(items) == 0:
				break
			for item in items:
				product = item.find('div', {'id': True})
				offer_block = product.find("ul", {"class": "product-promotions"})
				if offer_block:
					prod_a = product.find('a', {"data-auto": "product-tile--title"}) or \
					         product.find('a', {"class": "product-tile--title"})
					offer = offer_block.find(attrs={"class": "offer-text"})
					offer_dates_str = offer.next_sibling.contents[0].replace('Offer valid for delivery from ', '')
					offer_start_date = datetime.strptime(re.match('(\d{2}/\d{2}/\d{4})',
																offer_dates_str).group(1), date_format).date()
					offer_end_date = datetime.strptime(re.search('until (\d{2}/\d{2}/\d{4})',
																offer_dates_str).group(1), date_format).date()
					price_str = item.find_next(attrs={"class": "value"}).contents[0]
					discount, price_offered = calculate_discount(offer.contents[0], price_str)
					item_code = product.get('data-auto-id')
					if item_code:
						result[item_code] = Offer(item_name=str(prod_a.contents[0]), offer_name=str(offer.contents[0]),
													offer_dates_str=offer_dates_str, price_str=str(price_str),
													discount=discount, offer_start_date=offer_start_date,
													offer_end_date=offer_end_date, price_offered=price_offered,
													item_code=item_code)
						if discount is None:
							print(f'no discount for {item.contents[0]} : {item_code} offer')

			next_page += 1

		result_to_write = sorted(result.values(), key=lambda x: x.discount, reverse=True)
		filename_prefix = 'offers' + time.strftime("%y%m%d")
		suffix = '_all'

		def offer_to_str(item):
			return str(item.discount) + " ::: " + item.offer_name + " ::: " + item.price_str + " ::: " + \
					item.offer_dates_str + " ::: " + item.item_name + " ::: " + item.item_code + '\n'

		with open(filename_prefix + suffix + '.csv', 'w', encoding="utf8") as f:
			for item in result_to_write:
				f.write('+' + offer_to_str(item))


		result = filter_out(result)
		result_to_write = sorted(result.values(), key=lambda x: x.discount, reverse=True)
		suffix = '_filtered'

		with open(filename_prefix + suffix + '.csv', 'w', encoding="utf8") as f:
			for item in result_to_write:
				f.write('+' + offer_to_str(item))


		products_to_autoadd_filename = filename_prefix + suffix + '.csv'
		add_selected([products_to_autoadd_filename], driver)

	except Exception as e:
		import traceback
		traceback.print_exc()

	finally:
		if driver:
			driver.quit()

if __name__ == '__main__':
	sys.exit(scrap(sys.argv))
