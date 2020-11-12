
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import hashlib, re, random
from bs4 import BeautifulSoup
import time, os, pickle, sys, socket, json, configparser, warnings, base64, threading
from progress.bar import Bar
import ini
warnings.filterwarnings("ignore") 


if __name__ == "__main__":
	os.system("cls")
	if not os.path.isfile('config.ini'):
		config=open("./config.ini","w",encoding='utf-8')
		config.write('keywords="کرونا,کوید19,کروناویروس,ویروس کرونا"\r\ncount=10000\r\nheadless=yes\r\nexecutable_path=chromedriver.exe')
		config.close()
	config = ini.parse(open('./config.ini',encoding='utf-8').read())
	count = int(config['count'])
	if "," in config['keywords']:
		keywords=config['keywords'].split(',')
	else:
		keywords=config['keywords']
	options = Options()
	options.add_argument('--disable-logging') 
	if config['headless'] =='yes':
		options.add_argument('--headless')
	options.add_argument('--silent')
	options.add_argument('--disable-gpu') 
	driver = webdriver.Chrome(executable_path=config['executable_path'],chrome_options=options)
	if True:
		posts = []
		try:
			print("Logged Successfully...")
			main_link='https://twitter.com/search?q=%23{}&f=live'.format(keywords[0] if type(keywords) == list else keywords)
			driver.get(main_link)				
			not_complete=True
			while_counter=0
			unique_hash=[]
			bar = Bar('Processing', max=count)
			while not_complete:
				for keyword in keywords:
					main_link='https://twitter.com/search?q=%23{}&f=live'.format(keyword)
					try:
						if while_counter > 100:
							while_counter=0
							driver.get(main_link)
						else:
							while_counter+=1
						soup = BeautifulSoup(driver.page_source)
						tweets = soup.findAll(attrs={"data-testid" : "tweet"})
						for tweet in tweets:
							try:
								post={'text':'','media':'','link':'','author':{},'type':'text','hash':'','hashtags':''}
								photo =    tweet.find('div',attrs={'data-testid':'tweetPhoto'})
								video =    tweet.find('video')
								div=tweet.findAll('div')[1]
								author = div.findAll('a',attrs={'role':'link'})[0]
								post['link'] = "https://twitter.com{}".format(tweet.find_all("a", href=re.compile("/status/"))[0]['href'])
								post['datetime'] = tweet.find('time')['datetime']				
								post['author']={
									'name':'',
									'username':  author['href'].strip("/"),
									'avatar':author.findAll('img')[0]['src'], 
								}
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
											post['author']['name']=span.get_text()							
									post['hashtags'] = ",".join(hashtags)
									if photo is not None:
										post['type']='photo'
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
									bar.next()
									posts.append(post)
								if len(posts) >= count:
									not_complete=False
									print("Finish...")
									break
							except Exception as e:
								# print('Error in tweet for loop: \r\n{}'.format(str(e)))
								pass
						time.sleep(random.randint(1, 3))
						driver.execute_script("window.scrollTo(0,document.body.scrollHeight - {})".format(random.randint(1, 200)))
					except Exception as e:
						print('Error in while loop: \r\n{}'.format(str(e)))
		except Exception as e:
			print(str(e))
		finally:
			a=open('result.json','w+',encoding='utf-8')
			a.write(json.dumps(posts))
			a.close()
			print("{} post found and write to file!".format(len(posts)))
	elif "temporarily limited" in driver.page_source:
		print("We've temporarily limited some of your account features!\r\nPlease solve the recaptcha to continue...")
	else:
		print("Not Logged...")

