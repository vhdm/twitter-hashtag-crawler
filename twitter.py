
from datetime import datetime
from selenium import webdriver
import hashlib, re, random
from bs4 import BeautifulSoup
import time, os, pickle, sys, socket, json, configparser, warnings, base64, threading
from progress.bar import Bar
import ini
import urllib.request , socket
from stem import Signal
from stem.control import Controller
from selenium.webdriver.firefox.options import Options
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore") 


def switchIP():
    with Controller.from_port(port = 9051) as controller:
        controller.authenticate()
        controller.signal(Signal.NEWNYM)




def crawler(PROXY_HOST="127.0.0.1",PROXY_PORT=9050,posts=[],bar=None,config={},split_counter=0,unique_hash=[],keywords_stack=[],start_time=datetime.now()):
	# os.system("cls")
	last_reload_at=datetime.now()
	fp = webdriver.FirefoxProfile()
	count= int(config['count'])
	split= int(config['split'])
    # Direct = 0, Manual = 1, PAC = 2, AUTODETECT = 4, SYSTEM = 5
	fp.set_preference("network.proxy.type", 1)
	fp.set_preference("network.proxy.socks",PROXY_HOST)
	fp.set_preference("network.proxy.socks_port",int(PROXY_PORT))
	fp.update_preferences()
	options = Options()
	options.headless = True if config['headless'] =='yes' else False
	driver = webdriver.Firefox(options=options, firefox_profile=fp)
	try:
		driver.get("http://ifconfig.me/ip")
	except:
		print("Proxy server not runing...")
		driver.close()
		exit()
	html = driver.page_source
	soup = BeautifulSoup(html, 'lxml')
	print("\r\nTor IP: ",soup.find("pre").text)
	try:
		keyword=keywords_stack.pop()		
		# str_filter="(%23{})%20lang%3Afa%20since%3A2020-02-16%20-filter%3Alinks%20-filter%3Areplies&src=typed_query&f=live".format(keyword)
		str_filter="(%23{})%20lang%3Afa%20until%3A{}%20since%3A{}%20-filter%3Alinks%20-filter%3Areplies&src=typed_query&f=live".format(keyword,config['to_date'],config['from_date'])
		main_link='https://twitter.com/search?q={}'.format(str_filter)
		keywords_stack.insert(0,keyword)
		print("Stack: ",keywords_stack, keyword)
		driver.get(main_link)				
		while True:
			try:				
				time_diff_sec=(datetime.now() - last_reload_at).seconds
				if "Something went wrong." in driver.page_source or time_diff_sec > 50 or "No results for " in driver.page_source:
					switchIP()
					# diff_in_min = ((datetime.now() - start_time).seconds // 60) // bar.index
					# print("\r\nCrawl Speed: {} tpm(tweet per minute)".format(diff_in_min))
					print("\r\nSwitch Proxy...")
					print("\r\nPosts Count: {}, Diff In Sec: {}".format(len(posts),time_diff_sec))
					driver.close()
					crawler(posts=posts,bar=bar,config=config,split_counter=split_counter,unique_hash=unique_hash,keywords_stack=keywords_stack,start_time=start_time)
				soup = BeautifulSoup(driver.page_source)
				tweets = soup.findAll(attrs={"data-testid" : "tweet"})
				for tweet in tweets:
					try:
						post={'text':'','media':'','link':'','author_name':'','author_username':'','author_avatar':'','type':'text','hash':'','hashtags':''}
						photo =    tweet.find('div',attrs={'data-testid':'tweetPhoto'})
						video =    tweet.find('video')
						div=tweet.findAll('div')[1]
						if len(div.findAll('a',attrs={'role':'link'})) > 0:
							author = div.findAll('a',attrs={'role':'link'})[0]
						else:
							continue
						if type(tweet.find_all("a", href=re.compile("/status/"))) == list:
							post['link'] = "https://twitter.com{}".format(tweet.find_all("a", href=re.compile("/status/"))[0]['href'])
						if hasattr(tweet.find('time'),'datetime'):
							post['datetime'] = tweet.find('time')['datetime']
						else:
							continue
						post['author_name']=''
						post['author_username']=author['href'].strip("/")
						if author.findAll('img') == list and author.findAll('img')[0].get('src'):
							post['author_avatar']=author.findAll('img')[0]['src']							
						span_counter=0		
						fa_tweet=tweet.findAll('div',attrs={'lang':'fa'})
						hashtags=[]
						if fa_tweet is not None and len(fa_tweet) > 0 :
							fa_tweet=fa_tweet[0]
							for span in fa_tweet.findAll('span'):
								text=span.get_text().strip(" ")
								if "#" in text and text not in hashtags:
									hashtags.append(text)
								post['text']="{} {}".format(post['text'] , text)
							for span in tweet.findAll('span'):
								span_counter+=1
								if span_counter == 1:
									post['author_name']=span.get_text()							
							post['hashtags'] = ",".join(hashtags)
							if photo is not None:
								post['type']='photo'
								if hasattr(photo.find('img'),'src'):
									post['media'] = photo.find('img')['src']
							if video is not None:
								post['type']='video'
								post['media'] = video['src']				
							if post['text'] != '':
								post['hash'] = hashlib.md5(post['text'].encode('utf-8')).hexdigest()
							elif post['media'] != '':
								post['hash'] = hashlib.md5(post['media'].encode('utf-8')).hexdigest()
							else:
								continue
							if 	post['hash'] in unique_hash:
								continue
							unique_hash.append(post['hash'])
							last_reload_at = datetime.now()	
							bar.next()
							posts.append(post)
							if len(posts) >= count:
								df = pd.DataFrame.from_dict(posts)
								if config['type'] == 'csv':
									df.to_csv("{}data-{}-{}.csv".format(config['results_path'],split,split_counter))
								else:
									df.to_json("{}data-{}-{}.json".format(config['results_path'],split,split_counter))
								hash_file=open("{}unique-hashes.txt".format(config['results_path'],split,split_counter),'w')
								for hash in unique_hash:
									hash_file.write(str(hash)+'\n')
								hash_file.close()
								return True
							if len(posts)   >= int(split):
								split_counter+=1
								df = pd.DataFrame.from_dict(posts)
								if config['type'] == 'csv':
									df.to_csv("{}data-{}-{}.csv".format(config['results_path'],split,split_counter))
								else:
									df.to_json("{}data-{}-{}.json".format(config['results_path'],split,split_counter))
								hash_file=open("{}unique-hashes.txt".format(config['results_path'],split,split_counter),'w')
								for hash in unique_hash:
									hash_file.write(str(hash)+'\n')
								hash_file.close()
								posts=[]		
												
					except Exception as e:
						exc_type, exc_obj, exc_tb = sys.exc_info()
						fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
						print(exc_type, fname, exc_tb.tb_lineno)
				
				time.sleep(random.randint(1, 3))
				driver.execute_script("window.scrollTo(0,document.body.scrollHeight - {})".format(random.randint(1, 200)))
			except Exception as e:
				exc_type, exc_obj, exc_tb = sys.exc_info()
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
				print(exc_type, fname, exc_tb.tb_lineno)
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print(exc_type, fname, exc_tb.tb_lineno)
		exit()

if __name__ == "__main__":
	os.system("cls")
	start_time=datetime.now()
	print("Started At: {}".format(start_time.strftime("%Y-%m-%d %H:%M:%S")))
	
	if not os.path.isfile('config.ini'):
		path="{}\\results\\".format(os.getcwd())
		config=open("./config.ini","w",encoding='utf-8')
		os.makedirs(path)
		config.write('keywords="کرونا,ویروس‌کرونا,کوید_19,کوید19,کروناویروس,ویروس_کرونا"\ncount=20000\nheadless=no\ntype=csv\nsplit=1000\nresults_path="{}"\nfrom_date=2020-10-01\nto_date=2020-10-15'.format(path))
		config.close()
		print("Config File Generated... Run Again")
		exit(0)
	config = ini.parse(open('./config.ini',encoding='utf-8').read())
	count = int(config['count'])
	bar = Bar('Processing', max=count)
	unique_hash=[]
	if os.path.exists("{}unique-hashes.txt".format(config['results_path'])):
		with open("{}unique-hashes.txt".format(config['results_path']),'r',encoding='utf-8') as unique_hash_file:
			for line in unique_hash_file:
				unique_hash.append(line.replace("\n",""))
				bar.next()
			print("\r\nLoad Old Hashs [{}]".format(len(unique_hash)))
			time.sleep(3)

	keywords_stack=[]
	if "," in config['keywords']:
		keywords_stack=config['keywords'].split(',')
	else:
		keywords_stack=config['keywords']
	crawler(bar=bar,config=config,unique_hash=unique_hash,split_counter=len(unique_hash) // int(config['split']),keywords_stack=keywords_stack,start_time=start_time)
