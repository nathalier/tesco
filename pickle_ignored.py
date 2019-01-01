import pickle


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