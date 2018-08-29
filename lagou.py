#!/usr/bin/python
# -*- coding:utf-8 -*-
# author:joel 18-6-5
import pymongo
import re
import pandas
import requests
import time
import json
import random
import xlwt
import sys

class Tool():
    remove1 = re.compile('<h3.*?>|</h3>|<div.*?>|</div>|<p.*?>|</p>|<strong>|</strong>|<span.*?>|</span>')
    remove2 = re.compile('<a.*?>|</a>|\n')
    remove3 = re.compile('<br>|</br>')
    def replace(self,description):
        description = re.sub(self.remove1,"",description)
        description = re.sub(self.remove2,"",description)
        description = re.sub(self.remove3,"\n",description)
        return description.strip()

class Spider():
    def __init__(self):
        # self.keywords = raw_input(u'请输入想要应聘的职位名称：')
        self.url = 'https://www.lagou.com/jobs/positionAjax.json?needAddtionalResult=false'
        self.headers = {
            'Connection': 'keep-alive',
            'User-Agent': 'your-user-agent',
            # 'Host': 'www.lagou.com',
            # 'Origin': 'https://www.lagou.com',
            'Referer': 'https://www.lagou.com/jobs/list_%E7%88%AC%E8%99%AB%E5%B7%A5%E7%A8%8B%E5%B8%88?labelWords=&fromSearch=true&suginput=',
            'X-Requested-With': 'XMLHttpRequest'
        }
        self.cookies = {
            'Cookie': 'cookie'}
        self.tool = Tool()
        self.client = pymongo.MongoClient(host='localhost', port=port)
        self.db = self.client['lagou']

    def getHtml(self, url, datas):
        time.sleep(15+random.randint(1,20))
        result = requests.post(url, headers=self.headers, cookies=self.cookies, data=datas)
        requests.adapters.DEFAULT_RETRIES = 5
        time.sleep(5)
        print result.text
        data = json.loads(result.text)
        # print data
        return data

    def getPositionData(self, url, datas):
        datas = self.getHtml(url, datas)
        # print datas
        data = datas['content']['positionResult']['result']
        # print data
        allPosition = []
        for d in data:
            aPosition = {}
            # aPosition['businessZones'] = d['businessZones']
            secondUrl = 'https://www.lagou.com/jobs/'+str(d['positionId'])+'.html'
            print secondUrl
            #通过睡眠时间延迟访问速度，从而不被返回访问频繁，缺点在于爬取效率不高
            time.sleep(5+random.randint(1,10))

            r = requests.get(secondUrl,headers = self.headers)
            html =  r.text
            description = re.findall(r'<dd class="job_bt">(.*?)</dd>',html,re.S)
            des_locate = re.findall(r'<div class="work_addr">(.*?)</div>.*?<div id="miniMap">',html,re.S)
            #请求过多出现的验证码
            des1 = self.tool.replace(description[0])
            des2 = self.tool.replace(des_locate[0])
            des2 = des2.replace(' ','')[:-4] #除去字符串间的空格及最后的四个“查看地图”

            aPosition['description'] = des1
            aPosition['locate'] = des2
            aPosition['city'] = d['city']
            aPosition['companyFullName'] = d['companyFullName']
            aPosition['companyId'] = d['companyId']
            # aPosition['companyLabelList'] = d['companyLabelList']
            aPosition['companyLogo'] = d['companyLogo']
            aPosition['companyShortName'] = d['companyShortName']
            aPosition['companySize'] = d['companySize']
            aPosition['createTime'] = d['createTime']
            aPosition['district'] = d['district']
            aPosition['education'] = d['education']
            aPosition['firstType'] = d['firstType']
            aPosition['formatCreateTime'] = d['formatCreateTime']
            # aPosition['hitags'] = d['hitags']
            aPosition['industryField'] = d['industryField']
            # aPosition['industryLables'] = d['industryLables']
            aPosition['jobNature'] = d['jobNature']
            aPosition['linestaion'] = d['linestaion']
            aPosition['positionId'] = d['positionId']
            aPosition['positionName'] = d['positionName']
            aPosition['salary'] = d['salary']
            aPosition['workYear'] = d['workYear']
            allPosition.append(aPosition)
            time.sleep(5)
        return allPosition

    def saveData(self, url):
        self.keyword = raw_input(u'请输入想要应聘的职位名称：')#python爬虫实习
        # 将输入的keyword传入datas，post时
        page = int(raw_input(u'请输入想要获取的页数：'))
        self.time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print u'\n本地爬取时间：', self.time
        #第一次获取api数据时first为true
        datas = {'first': 'true',
                 'pn': "",
                 'kd': self.keyword}
        for p in range(1, page + 1):
            if p == 1:
                datas['pn'] = p
                print u'\n正在爬取第', p, u'页...'
                allPosition = self.getPositionData(url, datas)
                print len(allPosition)
                print u'\n爬取完毕'
                time.sleep(5)
                self.toMongoDB(allPosition, p)

            else:
                datas['first'] = 'false'
                datas['pn'] = p
                # datas['kd'] = keyword
                print u'\n正在爬取第', p, u'页...'
                allPosition = self.getPositionData(url, datas)
                print len(allPosition)
                print u'\n爬取完毕'
                time.sleep(5)
                self.toMongoDB(allPosition, p)

    def toMongoDB(self,allPosition,p):
        lg = self.db['lagou'+str(p)]
        lg.insert(allPosition)
        print u'第'+str(p)+u'页存储成功！'


spider = Spider()
#url为ajax加载的职位信息
url = 'https://www.lagou.com/jobs/positionAjax.json?needAddtionalResult=false'
spider.saveData(url)
