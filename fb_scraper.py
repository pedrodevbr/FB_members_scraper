import os
import datetime
import time
import json
import random
import _thread

from tqdm import tqdm 
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent

# Waiting time
time_wait = lambda x : time.sleep(3+random.random()*x)

def start_driver(url):

	ua = UserAgent()
	user_agent = ua.random
	
	chrome_options = Options()
	chrome_options.add_argument('--no-sandbox')
	chrome_options.add_argument('--window-size=1420,1080')
	chrome_options.add_argument('--disable-notifications')
	chrome_options.add_argument(f'user_agent={user_agent}')
	#chrome_options.add_argument('--headless')

	driver = webdriver.Chrome(ChromeDriverManager().install(),chrome_options=chrome_options)
	driver.maximize_window()
	try:
		driver.get(url)

		time_wait(1)
	except:
		print('-----ERROR opening browser-----')

	return driver

def code_to_class(temp):
	return '.'.join(temp.split(' '))

def get_credentials(file):
	try:
		with open(file,'r') as f:
			lines       = f.read().split('\n')
			email       = lines[0].split(':')[1]
			password    = lines[1].split(':')[1]
	except:
		print('-----ERROR in get_credentials-----')

	return email,password

def fill_by_ID(driver,field,info):
	time_wait(1)
	box     = driver.find_element_by_id(field)
	time_wait(1)
	box.send_keys(info)

def login(driver,email,password): 
	time_wait(3)
	try:
		fill_by_ID(driver,'email',email)
		fill_by_ID(driver,'pass',password)

		login_button = driver.find_element_by_name('login')
		login_button.click()
	except:
		print('-----ERROR in login-----')

def roll_down(driver,n):
	try:
		# Scroll down until it hits the end of the page
		print('Scrolling...')
		for i in range(n):
			driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
			time_wait(2)
		
	except:
		print('\n-----ERROR in scroll down-----')

email,password = get_credentials('credentials.txt')

url = 'https://www.facebook.com/'
driver = start_driver(url)

# Clear screen
#os.system('cls')

login(driver,email,password)

time_wait(3)
try:
	Alert(driver).dismiss()
except:
	pass

# Extract urls to scrape
with open('groups_to_scrape.txt', 'r') as f:
	urls = f.read().split('\n')

for url in urls:

	# Identifying if group or page
	if url.split('/')[3] == 'groups':
		with open("facebook_selectors_group.json") as sele:
			selectors = json.load(sele)
		if url.split('/')[-1]!='members': url+='/members'
		kind = 'group'
	else:
		with open("facebook_selectors_page.json") as sele:
			selectors = json.load(sele)
		if url.split('/')[-1]!='friends': url+='/friends'
		kind = 'page'

	driver.get(url)
	time_wait(4)
	group_name_class    = code_to_class(selectors['group_name_class'])
	group_name          = driver.find_element_by_class_name(group_name_class).text
	print(f'\n{kind} name: ',group_name)

	time_tag 	= datetime.datetime.now().strftime("%m-%d-%Y")
	file_name 	= f"{group_name}-{kind}-{time_tag}.csv"
	print('\nFile name: ',file_name)

	f = ''
	try:
		for file in os.listdir():
			if group_name in file:
				f = open(file_name,'rb')
	except:
		pass
	profiles_scraped = []
	if f =='':
		f = open(file_name,'wb')
		f.write('UserName, UserId, GroupName, GroupId, PhotoLink, Timestamp\n'.encode())
	else:
		lines = f.read().decode().split('\n')[1:]
		
		for line in lines:
			#print(line)
			if line!='':
				profiles_scraped.append(line.split(',')[1])

		print(f'\nProfiles from {group_name} scraped before = ',len(profiles_scraped))

	f.close()

	members_class   = code_to_class(selectors['group_members_class'])

	old_len = 1
	all_members = []
	no_more_members = False
	for test in range(3):
		#while True:
		#if old_len>2000: break
		print(old_len)
		k=0
		while len(all_members)<=old_len:

			roll_down(driver,5)
			all_members = driver.find_elements_by_class_name(members_class)
			if k==3:
				#print(f'{group_name} scraped completely')
				no_more_members = True
				break
			k+=1
		if no_more_members: break

		old_len = len(all_members)

		f = open(file_name,'ab')
		
		for member in all_members:

			try:
				if kind == 'page':
					userid   = member.find_element_by_tag_name('a').get_attribute('href')
					if userid in profiles_scraped: continue
					print(userid)
					username   = member.text.split('\n')[0]
					print(username)
					groupname = group_name
					print(groupname)
					groupid    = url.split('/')[3]
					print(groupid)
					photo      = member.find_element_by_tag_name('img').get_attribute('src')
					print(photo)
					timetag    =  datetime.datetime.now().strftime("%m/%d/%Y;%H:%M")
					print(timetag)
				elif kind == 'group':
					userid   = member.find_element_by_tag_name('a').get_attribute('href').split('/')[-2]
					if userid in profiles_scraped: continue
					print(userid)
					username   = member.text.split('\n')[0]
					print(username)
					groupname = group_name
					print(groupname)
					groupid    = url.split('/')[4]
					print(groupid)
					photo      = member.find_element_by_tag_name('image').get_attribute('xlink:href')
					print(photo)
					timetag    =  datetime.datetime.now().strftime("%m/%d/%Y;%H:%M")
					print(timetag)

				# Saving to file
				f.write(f'{username}, {userid}, {groupname}, {groupid}, {photo}, {timetag}\n'.encode())
				# Add to the scraped list
				profiles_scraped.append(userid)

			except:
				pass
		f.close()

	print(f"\nEnd of {group_name} scraping\n")

#driver.close()
#exit(0)