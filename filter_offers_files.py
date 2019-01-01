import sys
import re

from offer_scrapper import calculate_disc
from pickle_ignored import get_ignored, save_ignored


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
