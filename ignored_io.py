import json


def get_ignored():
	try:
		with open('ignore_offers.json', encoding="utf-8") as f:
			ignored = json.load(f)
	except FileNotFoundError:
		ignored = {"ignore_offers": [],
		           "ignore_products": [],
		           "not_intr_offers": {}}
	return set(ignored["ignore_offers"]), \
	       set(ignored["ignore_products"]), \
	       ignored["not_intr_offers"]


def save_ignored(ignore_offers, ignore_products, not_intr_offers):
	ignored = {"ignore_offers": list(ignore_offers),
	           "ignore_products": list(ignore_products),
	           "not_intr_offers": not_intr_offers}
	with open('ignore_offers.json', 'w', encoding="utf-8") as f:
		json.dump(ignored, f, ensure_ascii=False)
