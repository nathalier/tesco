import pickle
import sys
import re

from offer_scrapper import calculate_disc


pickle_file = 'ignore_promo.dat'


def get_ignored():
	try:
		with open(pickle_file, 'rb') as f:
			ignored = pickle.load(f)
			# ignore_offers, ignore_products, not_intr_offers = ignored
	except FileNotFoundError:
		ignored = [set(), set(), {}]
	return ignored


def save_ignored(ignored_list):
	with open(pickle_file, 'wb') as f:
		pickle.dump(ignored_list, f)


def filter_files(files):
	ignore_offers, ignore_products, not_intr_offers = get_ignored()

	for file in files:
		with open(file, encoding="utf8") as f:
			for offer in f:
				try:
					interested = re.search('^([\+\*\-]{1,2})', offer).group(1)
					prod_id = re.search('::: (\d*)$', offer).group(1)
					offer_text = re.search('::: (.*?) :::', offer).group(1)
					price_shown = re.search('::: .*? ::: (\d*\.\d*?) :::', offer).group(1)
					if interested == '-*':
						ignore_offers.add(offer_text)
					elif interested == '--':
						ignore_products.add(prod_id)
					elif interested == '-':
						price_offered = calculate_disc(offer_text, price_shown)[1]
						if prod_id not in not_intr_offers:
							not_intr_offers[prod_id] = price_offered
						elif price_offered < not_intr_offers[prod_id]:
							not_intr_offers[prod_id] = price_offered
				except AttributeError:
					pass

	save_ignored([ignore_offers, ignore_products, not_intr_offers])


if __name__ == '__main__':
	filter_files(sys.argv[1:])
