#!/usr/bin/env python
#-*-coding=utf-8-*-
'''
============================================
=======     Author : SenLief      ========== 
=======     Version : 0.1         ==========
============================================

功能：小说抓取最新章节并保存到文件中
原理：利用笔趣阁手机端抓取小说。
		 手机端采用的是Cookies方式保存书籍，添加看到章节的书签到书架，利用抓取书架来比对最新章节
		 和书签地址是否相同。

Bug：
	1、书签url不对会死循环。

TODO:
	1、解决Bug
	2、处理写到文件的格式问题
   -3、合并生成的文件到一个文件中
	4、分量抓取
'''

import os
import os.path
import sys
import re
import time
import requests
import ConfigParser
from bs4 import BeautifulSoup
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

reload(sys)
sys.setdefaultencoding('utf-8')


headers = {
                 'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:47.0) Gecko/20100101 Firefox/47.0' ,
                 'Connection' : 'keep-alive',
                 'Accept'         : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                 'Accept-Encoding' : 'gzip, deflate, sdch',
                 'Accept-Language' : 'zh-CN,zh;q=0.8'
         }

def get_case(cookies):
	'''
		获取书籍书架，比对最新章节和书签url。
		返回一个生成器的元祖。eg : （"/book/1/700033.html"，"/book/1/700023.html"）
	'''	
	resp = requests.get('http://m.biquge.la/shu.php',cookies=cookies,headers=headers)
	resp.encoding = 'gbk'
	
	soup = BeautifulSoup(resp.text, 'lxml')
	caseList = soup.find_all(href=re.compile(r"html$"))
	while len(caseList) > 1 :
		nId = caseList[0]['href'].split('/')[2]
		cId = caseList[1]['href'].split('/')[2]
		
		if nId == cId:
			yield (caseList[0]['href'],caseList[1]['href'])
			del caseList[:2]
		else:
			yield (caseList[0]['href'],caseList[0]['href'])
			del caseList[:1]
	else:
		yield (caseList[0]['href'],caseList[0]['href'])

def get_index(cid):
	'''
		获取书籍目录。
		接受一个书籍cid
		返回一个生成器的目录地址。 eg : "/book/1/700033.html"
	'''

	indexUrl = 'http://m.biquge.la/booklist/' + str(cid) +'.html'
	indexResp = requests.get(indexUrl,headers=headers)
	indexResp.encoding = 'gbk'

	soup = BeautifulSoup(indexResp.text, 'lxml')
	indexList = soup.find_all(href=re.compile(r'^\/book.*html$'))
	for url in indexList:
		yield url['href']

def catch(url):
	'''
		抓取章节内容。
		接受章节url参数，一般由下面的 index_num()函数生成
		返回章节内容。
	'''
	
	resp = requests.get(url,headers=headers)
	resp.encoding = 'gbk'
	
	soup = BeautifulSoup(resp.text,'lxml')
	title = soup.find(id='nr_title').text
	content = soup.find(id='nr1').text
	content = title +  content.replace('shipei_x()',' ').strip()
	return content

def index_num(caseUrl):
	'''
		获取需要抓取的地址，并抓取写到文件中。
		接受参数为一个元祖变量，一般有get_case()函数返回.
	'''
	
	bookId = caseUrl[0].split('/')[2]	
	n = 0 
	for url in get_index(bookId):	
		if caseUrl[0] == caseUrl[1]:
			catchUrl = 'http://m.biquge.la' + caseUrl[0]
			with open(bookId + '.txt', 'a+') as f:
				f.write(catch(catchUrl))
			break
		elif url == caseUrl[1]:
			catchUrl = 'http://m.biquge.la' + url
			with open(bookId + '_' + str(n) + '.txt', 'a+') as f:
				f.write(catch(catchUrl))
			break
		else:
			catchUrl = 'http://m.biquge.la' + url
			with open(bookId + '_' + str(n) + '.txt', 'a+') as f:
				f.write(catch(catchUrl))
			n = n + 1
	print n 		
	if n != 0 :
		with open(bookId + '.txt', 'a+') as f:
			while n >= 0:
				with open(bookId + '_' + str(n) + '.txt','r') as fp:
					for line in fp.readlines():
						f.write('\n' + line)
				os.remove(bookId + '_' + str(n) + '.txt')
				n = n - 1
	else:
		pass

def main():
	'''
		多线程并行入口。读取配置文件，多线程抓取书籍。
	'''
	cf = ConfigParser.ConfigParser()
	cf.read("config.ini")
	ck = {k:v for k,v in cf.items("cookies")}
	ckid = {'cookie[{cid}]'.format(cid=cid) : newurl for cid, newurl in cf.items("books")}
	ck.update(ckid)
	
	if os.path.exists("books"):
		os.chdir("books")
	else:
		os.mkdir("books")
		os.chdir("books")

	pool = ThreadPool(5)
	pool.map(index_num, get_case(ck))
	pool.close()
	pool.join()

if __name__ == '__main__':
	main()
