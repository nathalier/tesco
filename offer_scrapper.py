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


def calculate_discount(offer, price):
	def norm(p):
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
		driver = webdriver.Chrome()
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
			items = product_list.find_all('a', {"data-auto": "product-tile--title"})
			if not items:
				items = product_list.find_all('a', {"class": "product-tile--title"})
			if len(items) == 0:
				break
			for item in items:
				offer_block = item.parent.next_sibling.find("ul", {"class": "product-promotions"})
				if offer_block:
					offer = offer_block.find(attrs={"class": "offer-text"})
					offer_dates_str = offer.next_sibling.contents[0].replace('Offer valid for delivery from ', '')
					offer_start_date = datetime.strptime(re.match('(\d{2}/\d{2}/\d{4})',
																offer_dates_str).group(1), date_format).date()
					offer_end_date = datetime.strptime(re.search('until (\d{2}/\d{2}/\d{4})',
																offer_dates_str).group(1), date_format).date()
					price_str = item.find_next(attrs={"class": "value"}).contents[0]
					discount, price_offered = calculate_discount(offer.contents[0], price_str)
					item_code = re.search('/(\d+)$', item['href']).group(1)
					if item_code:
						# 			format:  {"item_code": (name_of_item : str, name_of_offer : str, offer_dates_str : str,
						#                           price_str : str, discount : float,
						#                           offer_start_date : datetime, offer_end_date : datetime,
						#                           price_offered : float, item_code : str)}
						result[item_code] = Offer(item_name=str(item.contents[0]), offer_name=str(offer.contents[0]),
													offer_dates_str=offer_dates_str, price_str=str(price_str),
													discount=discount, offer_start_date=offer_start_date,
													offer_end_date=offer_end_date, price_offered=price_offered,
													item_code=item_code)
						if discount is None:
							print(f'no discount for {item.contents[0]} : {item_code} offer')

			next_page += 1
			# if next_page == 3:
			# 	break

		################
		# import pickle
		# pickle_f = 'temp.dat'
		# with open(pickle_f, 'rb') as f:
		# 	result = pickle.load(f)
		################


		result = filter_out(result)

		result = sorted(result.values(), key=lambda x: x.discount, reverse=True)
		filename_prefix = 'offers' + time.strftime("%y%m%d")
		all_suffix = '_all'
		new_suffix = '_after_' + start_date.strftime("%m%d")
		ending_suffix = '_ending'

		def offer_to_str(item):
			return str(item.discount) + " ::: " + item.offer_name + " ::: " + item.price_str + " ::: " + \
					item.offer_dates_str + " ::: " + item.item_name + " ::: " + item.item_code + '\n'

		with open(filename_prefix + all_suffix + '.csv', 'w', encoding="utf8") as f:
			for item in result:
				f.write('+' + offer_to_str(item))

		# with open(filename_prefix + new_suffix + '.csv', 'w', encoding="utf8") as f:
		# 	for item in filter(lambda x: x[1][5] >= start_date, result):
		# 		f.write(offer_to_str(item))
		#
		# with open(filename_prefix + ending_suffix + '.csv', 'w', encoding="utf8") as f:
		# 	for item in filter(lambda x: x[1][6] <= ending_soon_date, result):
		# 		f.write(offer_to_str(item))
		#
		# with open(filename_prefix + new_suffix + '_or_' + ending_suffix + '.csv', 'w', encoding="utf8") as f:
		# 	for item in filter(lambda x: x[1][5] >= start_date or x[1][6] <= ending_soon_date, result):
		# 		f.write(offer_to_str(item))

		products_to_autoadd_filename = filename_prefix + all_suffix + '.csv'
		add_selected([products_to_autoadd_filename], driver)

	except Exception as e:
		import traceback
		traceback.print_exc()

	finally:
		if driver:
			driver.quit()

if __name__ == '__main__':
	sys.exit(scrap(sys.argv))
