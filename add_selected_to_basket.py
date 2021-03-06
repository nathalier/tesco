__author__ = 'Nathalie'

import credentials
import sys, time, re, glob
from selenium import webdriver
from selenium.webdriver import  ActionChains
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


login_url = 'https://secure.tesco.com/account/en-GB/login?from=/'
fav_url = 'https://www.tesco.com/groceries/en-GB/favorites'
fav_trunc_url = '/groceries/en-GB/favorites?page='
product_base_url = 'https://www.tesco.com/groceries/en-GB/products/'
account = credentials.account
passw = credentials.passw


def driver_login():
	driver = webdriver.Firefox()
	driver.get(login_url)
	login_input = driver.find_element(By.ID, 'username')
	login_input.send_keys(account)
	login_passw = driver.find_element(By.ID, 'password')
	login_passw.send_keys(passw)
	login_passw.send_keys(Keys.ENTER)
	time.sleep(3)
	return driver


def add_selected(file_list, driver):
	for file_name in file_list:
		with open(file_name) as f:
			for line in f.readlines():
				if line.startswith('+'):
					url = product_base_url + re.search('::: (\d*)$', line).group(1)
					driver.get(url)
					try:
						close_cookie_btn = driver.find_element(By.CLASS_NAME, 'cookie-policy__button')
						close_cookie_btn.click()
					except NoSuchElementException:
						pass
					# elem_to_scroll_to = driver.find_element(By.CLASS_NAME, 'write-a-review')
					# ActionChains(driver).move_to_element(elem_to_scroll_to).perform()
					# driver.execute_script("arguments[0].scrollIntoView();", elem_to_scroll_to)
					# time.sleep(2)
					try:
						add_btn = driver.find_element(By.XPATH,\
						'//*[contains(@class, "grocery-product")]//button[@type="submit" and //*[text() = "Add"]]')
						add_btn.click()
					except NoSuchElementException:
						pass
					except ElementNotInteractableException:
						print('ElementNotInteractableException: ' + url)
					time.sleep(1)


if __name__ == '__main__':
	try:
		driver = driver_login()

		files = []
		if len(sys.argv) > 1:
			files.extend(sys.argv)
		else:
			files.extend(glob.glob('./offers' + time.strftime("%y%m%d") + '*.csv'))

		add_selected(files, driver)
		driver.quit()
	except:
		if driver:
			driver.quit()
