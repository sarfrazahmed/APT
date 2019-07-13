from selenium import webdriver
import os
import time

os.chdir('F:\APT\Scripts')
driver = webdriver.Chrome()
page = driver.get('https://kite.zerodha.com/')

# Logging in using user credential
user_id_box = driver.find_element_by_xpath('//*[@id="container"]/div/div/div/form/div[2]/input')
password_box = driver.find_element_by_xpath('//*[@id="container"]/div/div/div/form/div[3]/input')
log_in_button = driver.find_element_by_xpath('//*[@id="container"]/div/div/div/form/div[4]/button')
user_id_box.send_keys('UD8801')
password_box.send_keys('zaq12345')
log_in_button.click()
time.sleep(10)

# Putting Secondary wed2f4
pin_box = driver.find_element_by_xpath('//*[@id="container"]/div/div/div/form/div[2]/div/input')

continue_box = driver.find_element_by_xpath('//*[@id="container"]/div/div/div/form/div[3]/button')
pin_box.send_keys('555555')
continue_box.click()



