#!/usr/bin/env python
#-*-coding=utf-8-*-

import os
import os.path
import sys
import re
import requests
import ConfigParser
from bs4 import BeautifulSoup
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

reload(sys)
sys.setdefaultencoding('utf-8')

'''
重写书籍抓取部分,利用笔趣阁书架的功能来完善书籍判断部分。主要抓取手机站，不再抓取电脑端。

1、登录部分
2、搜索书籍，返回书籍url地址（暂时不做）
3、获取书籍目录并加入书架，添加最新章节为书签。
4、实现书籍抓取，返回抓取内容
5、流控：
	1、遍历我的书架，判断最新章节和书签是否一致，一致则不抓取
	2、不一致判断章节是否只有一章，一章则直接抓取
	3、不是一章则和目录比对章节看有几章则抓取几章
6、实现邮件推送服务
'''
headers = {
                 'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:47.0) Gecko/20100101 Firefox/47.0' ,
                 'Connection' : 'keep-alive',
                 'Accept'         : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                 'Accept-Encoding' : 'gzip, deflate, sdch',
                 'Accept-Language' : 'zh-CN,zh;q=0.8'
         }

def get_case(cookies):
	
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

	indexUrl = 'http://m.biquge.la/booklist/' + str(cid) +'.html'
	indexResp = requests.get(indexUrl,headers=headers)
	indexResp.encoding = 'gbk'

	soup = BeautifulSoup(indexResp.text, 'lxml')
	indexList = soup.find_all(href=re.compile(r'^\/book.*html$'))
	for url in indexList:
		yield url['href']

def catch(url):

	# url = 'http://m.biquge.la/book/511/7088514.html'
	resp = requests.get(url,headers=headers)
	resp.encoding = 'gbk'
	
	soup = BeautifulSoup(resp.text,'lxml')
	title = soup.find(id='nr_title').text
	content = soup.find(id='nr1').text
	content = title + '\n' +  content.replace('shipei_x()',' ')
	return content

def index_num(caseUrl):

	# for cUrl, nUrl in get_case():
	bookId = caseUrl[0].split('/')[2]	
	n = 0 
	for url in get_index(bookId):	
		if caseUrl[0] == caseUrl[1]:
			catchUrl = 'http://m.biquge.la' + caseUrl[0]
			# print catch(catchUrl)
			with open(bookId + '.txt', 'a+') as f:
				f.write(catch(catchUrl))
			break
		elif url == caseUrl[1]:
			catchUrl = 'http://m.biquge.la' + url
			# print catch(catchUrl)
			with open(bookId + '.txt', 'a+') as f:
				f.write(catch(catchUrl))
			break
		else:
			catchUrl = 'http://m.biquge.la' + url
			# print catch(catchUrl)
			with open(bookId + '_' + str(n) + '.txt', 'a+') as f:
				f.write(catch(catchUrl))
			n = n + 1

def main():
	
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


main()