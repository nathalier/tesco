__author__ = 'Nathalie'

def clear_ids(filename='ids.txt'):
	with open(filename) as f:
		ids = map(int, f.read().split(','))
	ids = sorted(set(ids))
	ids = map(str, ids)
	with open('ids_set.txt', 'w') as f:
		f.write(', '.join(ids))

if __name__ == 'main':
	clear_ids()
