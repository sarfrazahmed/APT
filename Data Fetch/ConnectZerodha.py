from selenium import webdriver
import os
import time
import configparser

config = configparser.ConfigParser()
config_path = 'E:/Stuffs/APT/APT/Paper Trading/config.ini'
config.read(config_path)

api_key = config['API']['API_KEY']
api_secret = config['API']['API_SECRET']
username = config['USER']['USERNAME']
password = config['USER']['PASSWORD']
pin = config['USER']['PIN']
homepage = 'https://kite.zerodha.com/'

path = 'F:/APT/Scripts'
os.chdir(path)
driver = webdriver.Chrome()
page = driver.get(homepage)

# Logging in using user credential
user_id_box = driver.find_element_by_xpath('//*[@id="container"]/div/div/div/form/div[2]/input')
password_box = driver.find_element_by_xpath('//*[@id="container"]/div/div/div/form/div[3]/input')
log_in_button = driver.find_element_by_xpath('//*[@id="container"]/div/div/div/form/div[4]/button')
user_id_box.send_keys(username)
password_box.send_keys(password)
log_in_button.click()
time.sleep(10)

# Putting Secondary wed2f4
pin_box = driver.find_element_by_xpath('//*[@id="container"]/div/div/div/form/div[2]/div/input')

continue_box = driver.find_element_by_xpath('//*[@id="container"]/div/div/div/form/div[3]/button')
pin_box.send_keys(pin)
continue_box.click()



