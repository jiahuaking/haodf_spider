import csv
import datetime
import os
from time import *
import json
import re
import requests
from lxml import etree


class Haodf():
    # 初始化浏览器
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
        }

    # 获取医生个人网站首页、预约挂号、出诊时间、患者分享、科普文章、在线咨询、个人网站统计数据六个网站的url
    def doctor_pageone(self, jibing):
        # 爬取开始之前，先做是否爬取过的判断，取出已爬取医生的列表
        rootDir = "data" + str(jibing) + "_doctor_html"
        finished = []  # 已经完成列表
        for parent, dirnames, filenames in os.walk(rootDir):
            for filename in filenames:
                finished.append(filename)

        # 打开urls文件，按行取出医生url
        f = open('data/' + str(jibing) + '_doctor_urls', 'r', encoding='utf-8')
        while True:
            # 若读取到文件最尾端，跳出循环，结束爬虫
            line = f.readline()
            if not line:
                break

            # 判断该医生是否爬取过，若爬取过，则跳出此次循环，进入下一个医生
            url = line.replace('\n', '')
            finished_id = url.replace('https://', '').replace('.haodf.com/', '')
            if finished_id in finished:
                print('该医生个人网站的信息已经爬取过~')
                continue
            print('------', url, '------')

            # 声明一个doctor_detail列表，用于存放1.医生个人网站首页数据；2.医生“预约挂号”网站信息；3.医生个人网站统计数据；
            doctor_detail = []
            doctor_id = url.replace('https://', '').replace('.haodf.com/', '')
            doctor_detail.append(doctor_id)
            # 解析个人网站首页医生数据: 10个属性
            if self.headers.get('Cookie'):
                del self.headers['Cookie']
            _resp = requests.get(url, headers=self.headers)
            resp = _resp.text
            self.headers['Cookie'] = '__jsluid_s=' + _resp.cookies.get('__jsluid_s')
            content = etree.HTML(resp)
            beginweb_detail = self.parse_beginweb(content)
            doctor_detail.extend(beginweb_detail)
            # 取出医生姓名，方便打印查看爬虫进展
            doctor_name = beginweb_detail[0]
            # 进入个人网站统计数据爬取并解析：13个属性
            doctor_url = ''.join(url).strip()
            if len(doctor_url) > 0:
                print('正在爬取', doctor_name, '医生个人网站--链接：', doctor_url)
                selfweb_detail = self.get_selfweb(doctor_url, doctor_name, resp)
                doctor_detail.extend(selfweb_detail)
            else:
                selfweb_detail = [''] * 13
                doctor_detail.extend(selfweb_detail)
                print(doctor_name, '---医生未开通个人网站---')

            # 获取"医生预约挂号"按钮的url，进入“预约挂号”网站爬取信息并解析
            appointment_url = content.xpath(
                '//div[@class="container service-outer"]/ul[@class="clearfix"]/li[3]/a/@href')
            if len(appointment_url) > 0:
                appointment_url = ''.join(appointment_url).strip()
                print('正在爬取', doctor_name, '医生预约挂号网站--链接：', appointment_url)
                appointment_detail = self.get_appointmentweb(appointment_url, doctor_name)
                doctor_detail.extend(appointment_detail)
            else:
                appointment_detail = ['']
                doctor_detail.extend(appointment_detail)
                print(doctor_name, '---医生未开通预约挂号服务---')

            print(doctor_name, '医生个人信息为：', doctor_detail)
            self.doctor_detail(jibing, doctor_detail)  # ------------------写入文件--------------

            # 获取“医生出诊时间”按钮的url，进入“出诊时间”网站爬取信息并解析
            allvisit_url = content.xpath('//section[@class="container"][1]/header/h2/a/@href')
            if len(allvisit_url) > 0:
                allvisit_url = ''.join(allvisit_url).strip()
                print('正在爬取', doctor_name, '医生出诊时间网站--链接：', allvisit_url)
                self.get_visitweb(jibing, allvisit_url, doctor_id, doctor_name)
            else:
                print(doctor_name, '---医生未公布出诊信息---')

            # 获取“患者全部分享”按钮的url,进入“全部分享”网站爬取信息并解析
            allshare_url = content.xpath('//section[@class="container"][2]/header/a/@href')
            print('正在爬取', doctor_name, '医生分享网站--链接：', allshare_url)
            if len(allshare_url) > 0:
                self.get_shareweb(jibing, allshare_url, doctor_id, doctor_name)

            # 获取“医生科普文章”按钮的url,进去“科普文章”网站爬取信息并解析
            allpaper_url = content.xpath('//section[@class="container"]/header/h2/a[@href="/lanmu"]/@href')
            if len(allpaper_url) > 0:
                allpaper_url = str(url) + str(allpaper_url[0])
                print('正在爬取', doctor_name, '医生科普文章网站--链接：', allpaper_url)
                self.get_paperweb(jibing, allpaper_url, doctor_id, doctor_name)
            else:
                print(doctor_name, '---医生未发表科普文章---')

            # 获取“医生在线问诊”按钮的url，进入“在线咨询”网站爬取信息并解析
            allzixun_url = content.xpath('//section[@class="container"]/header/h2/a[@href="/zixun/list.htm"]/@href')
            if len(allzixun_url) > 0:
                allzixun_url = str(url) + str(allzixun_url[0])
                print('正在爬取', doctor_name, '医生在线咨询网站--链接：', allzixun_url)
                self.get_zixunweb(jibing, allzixun_url, doctor_name)

            # 医生个人信息（除全部分享站）解析存储后将爬取网页和记录写入html文件夹，以便下次判断是否爬取过，避免重复爬取
            self.finished(jibing, finished_id, content)

        f.close()


    def finished(self, jibing, finished_id, content):
        doctor_detail_html = etree.tostring(content).decode('utf-8')
        f = open("data" + str(jibing) + "_doctor_html/" + finished_id, "w", encoding = "utf-8")
        f.write(doctor_detail_html)
        f.close()


    # 解析医生个人网站首页信息的数据
    def parse_beginweb(self, content):  # 这里添加字段
        # 姓名
        name = content.xpath('//div[@class="profile-txt"]/h1[@class="doctor-name"]/text()')
        name = ''.join(name).strip()
        # print(name)
        # 科室
        department = content.xpath('//div[@class="profile-txt"]/ul/li[@class="doctor-faculty"]/a[1]/text()')
        department = ''.join(department).strip()
        # print(department)
        # 医学职称
        medical_title = content.xpath('//div[@class="profile-txt"]/span[@class="doctor-title"]/text()')
        medical_title = ''.join(medical_title)
        # print(medical_title)
        # 学术职称
        academic_title = content.xpath('//div[@class="profile-txt"]/span[@class="doctor-educate-title"]/text()')
        academic_title = ''.join(academic_title).strip()
        # print(academic_title)
        # 擅长
        good_at = content.xpath('//div[@class="brief-container"]/div[@class="clearfix"][1]/div/p/text()')
        good_at = ''.join(good_at).strip().replace('\n', '')
        # print(good_at)
        # 职业经历
        job = content.xpath('//div[@class="brief-container"]/div[@class="clearfix"][2]/div/p/text()')
        job = ''.join(job).strip().replace('\n', '')
        # print(job)
        # 推荐热度
        recommend = content.xpath('//ul[@class="profile-statistic"]/li[1]/span[@class="value"]/text()')
        recommend = ''.join(recommend).strip()
        # print(recommend)
        # 提供服务
        services = content.xpath(
            '//div[@class="container service-outer"]/ul[@class="clearfix"]/li[@class="service-item"]/a/text()')
        services = ''.join(services).strip().replace('\n                    ', '/').replace('//    ', '/').replace('//    ', '/')
        # print(services)
        # 疗效满意度
        efficacy_satisfaction = content.xpath('//div[@class="satisfaction clearfix"]/div[1]/i/text()')
        efficacy_satisfaction = ''.join(efficacy_satisfaction).strip()
        # print(efficacy_satisfaction)
        # 态度满意度
        attitude_satisfaction = content.xpath('//div[@class="satisfaction clearfix"]/div[2]/i/text()')
        attitude_satisfaction = ''.join(attitude_satisfaction).strip()
        # print(attitude_satisfaction)

        beginweb_detail = []
        beginweb_detail.extend([name, department, medical_title, academic_title, good_at, job, recommend, services,
                                efficacy_satisfaction, attitude_satisfaction])
        print(name, '医生个人网站首页信息：', beginweb_detail)
        return beginweb_detail


    # 爬取医生预约挂号网站信息
    def get_appointmentweb(self, appointment_url, doctor_name):
        # 模拟浏览器访问“预约挂号”的网页
        content = etree.HTML(requests.get(appointment_url, headers=self.headers).text)
        # sleep(1)

        appointments = content.xpath(
            '//ul[@class="r-c-list"]/li[@class="r-c-item clearfix"]/div[@class="r-c-i-info"]/p[@class="r-c-i-count"]')
        appointment_detail = []
        for i in range(len(appointments)):
            appointment = appointments[i]

            # 预约转诊量
            referrals = appointment.xpath('./span/text()')
            referrals = ''.join(referrals).strip()
            # print(referrals)

            appointment_detail.extend([referrals])
        print(doctor_name, '医生预约挂号信息：', appointment_detail)
        return appointment_detail


    # 爬取医生出诊时间网站信息
    def get_visitweb(self, jibing, allvisit_url, doctor_id, doctor_name):
        # 模拟浏览器访问“出诊时间”的网页
        content = etree.HTML(requests.get(allvisit_url, headers=self.headers).text)
        # sleep(10)

        visits = content.xpath('//li[@class="menzhen-ul-li"]')
        for i in range(len(visits)):
            visit = visits[i]

            # 日期
            date = visit.xpath('./div[@class="time"]/p[1]/text()')
            date = ''.join(date).strip()
            # print(date)
            # 星期
            week = visit.xpath('./div[@class="time"]/p[2]/text()')
            week = ''.join(week).strip()
            # print(week)
            # 医院
            hospital = visit.xpath('./div[@class="info"]/ul/li[1]/h2/text()')
            hospital = ''.join(hospital).strip()
            # print(hospital)
            # 地点
            location = visit.xpath('./div[@class="info"]/ul/li[1]/h2/a/text()')
            location = ''.join(location).strip()
            # print(location)
            # 科室
            department = visit.xpath('./div[@class="info"]/ul/li[2]/p[2]/text()')
            department = ''.join(department).strip()
            # print(department)
            # 门诊类型
            type = visit.xpath('./div[@class="info"]/ul/li[3]/p[2]/text()')
            type = ''.join(type).strip()
            # print(type)

            doctor_visits = []
            doctor_visits.extend([doctor_id, doctor_name, date, week, hospital, location, department, type])
            print(doctor_name, '医生出诊时间网站内容：', doctor_visits)
            self.doctor_visits(jibing, doctor_visits)  # -----------------------医生出诊网页信息-------------


    # 爬取患者分享网站的患者分享内容
    def get_shareweb(self, jibing, allshare_url, doctor_id, doctor_name):
        # 获取“全部分享”的完整url
        allshare_url = ''.join(allshare_url).strip()
        # 模拟浏览器访问“全部分享”的网页
        content = etree.HTML(requests.get(allshare_url, headers=self.headers).text)

        # 获得全部分享-分页数量
        page_num = content.xpath('//a[@class="p_text"]/text()')
        if len(page_num) > 0:
            page_num = ''.join(page_num).strip().split('共')[1].split('页')[0]
            page_num = int(page_num)
            print(doctor_name, '医生共有', str(page_num), '页患者就诊记录分享')
        else:
            page_num = int(1)
            print(doctor_name, '医生共有', str(page_num), '页患者就诊记录分享')

        # 翻页爬取全部分享的内容
        for i in range(1, page_num + 1):
            url = allshare_url.split('.htm')[0]
            url = url + '/' + str(i) + '.htm'
            response = requests.get(url, headers=self.headers)
            # sleep(10)

            print('正在爬取第' + str(i) + '页的全部分享的url: ', url)
            content1 = etree.HTML(response.text)
            tables = content1.xpath('//div[@class ="item-body"]/div[@class="patient-eva"]')
            for j in range(len(tables)):
                table = tables[j]

                # 投票时间
                date = table.xpath('./div[@class="eva-footer clearfix"]/div[@class="evaluate-date"]/text()')
                date = ''.join(date).strip()
                if '今天' in date:
                    date = datetime.date.today()
                else:
                    date = date
                # 患者
                patient_name = table.xpath('./div[@class="patient-eva-header"]/span[1]/text()')
                patient_name = ''.join(patient_name).strip().split('：')[1]
                # print(patient_name)
                # 所患疾病
                disease = table.xpath('./div[@class="patient-eva-header"]/a/span/text()')
                disease = ''.join(disease).strip()
                # print(disease)
                # 看病目的
                aim = table.xpath('./div[@class="clearfix"]/span[1]/text()')
                aim = ''.join(aim).strip().split('：')[1]
                # print(aim)
                # 治疗方式
                way = table.xpath('./div[@class="clearfix"]/span[2]/text()')
                way = ''.join(way).strip().split('：')[1]
                # print(way)
                # 患者主观疗效
                effect = table.xpath('./div[@class="clearfix"]/span[3]/text()')
                if len(effect) == 0:
                    effect = '未填写'
                else:
                    effect = ''.join(effect).strip()
                # print(effect)
                # 态度
                attitude = table.xpath('./div[@class="clearfix"]/span[4]/text()')
                if len(effect) == 0:
                    attitude = '未填写'
                else:
                    attitude = ''.join(attitude).strip()
                # print(attitude)
                # 费用总计
                fee = table.xpath('./div[@class="clearfix"]/span[5]/text()')
                fee = ''.join(fee).strip()
                # print(fee)
                # 病情状态
                state = table.xpath('./div[@class="clearfix"]/span[6]/text()')
                state = ''.join(state).strip()
                # print(state)
                # 就诊理由
                reason = table.xpath('./div[@class="clearfix"]/span[7]/text()')
                reason = ''.join(reason).strip()
                # print(reason)
                # 标签
                tag = table.xpath('./div[@class="trait-bd"]/div[@class="trait"]/text()')
                tag = '/'.join(tag).strip()
                # print(tag)
                # 看病经验/感谢信
                experience_thank = table.xpath('./div[@class="eva-detail"]/text()')
                experience_thank = ''.join(experience_thank).strip().replace(' ', '')
                # print(experience_thank)

                doctor_share = []
                doctor_share.extend(
                    [doctor_id, doctor_name, patient_name, disease, aim, way, effect, attitude, tag, experience_thank,
                     date, reason, state, fee])
                print(doctor_name, '患者分享网站的信息：', doctor_share)
                self.doctor_share(jibing, doctor_share)  # -----------------------分享网页全部患者信息-------------


    # 爬取医生科普文章网站列表url
    def get_paperweb(self, jibing, allpaper_url, doctor_id, doctor_name):
        # 模拟浏览器访问“科普文章”的网页
        content = etree.HTML(requests.get(allpaper_url, headers=self.headers).text)
        # sleep(10)

        # 获取科普文章-分页数量
        page_num = content.xpath(
            '//div[@class="page_main"]/div[@class="page_turn"]/a[@class="page_turn_a" and @rel="true"]/text()')
        if len(page_num) > 0:
            page_num = ''.join(page_num).strip().split('共')[1].split('页')[0]
            page_num = int(page_num)
            print(doctor_name, '医生共有', str(page_num), '页科普文章')
        else:
            page_num = int(1)
            print(doctor_name, '医生共有', str(page_num), '页科普文章')

        # 翻页爬取全部的科普文章
        for i in range(1, page_num + 1):
            paper_url = allpaper_url + str('_') + str(i)
            response = requests.get(paper_url, headers=self.headers)
            # sleep(10)

            print('正在爬取第' + str(i) + '页的科普文章url: ', paper_url)
            content1 = etree.HTML(response.text)
            papers = content1.xpath('//ul[@class="article_ul"]/li')

            for j in range(len(papers)):
                paper = papers[j]
                # 文章类型
                # 先判断是否为“引用文章”
                type = paper.xpath('./div[@class="clearfix"]/p[@class="art_title"]/font/text()')
                # 如果不是“引用文章”
                if len(type) == 0:
                    type = paper.xpath('./div[@class="clearfix"]/p[@class="art_title"]/a[1]/text()')
                    type = ''.join(type).strip().split('[')[1].split(' ')[0]
                    # print(type)
                # 如果是“引用文章”
                else:
                    type = type
                    type = ''.join(type).strip().split('[')[1].split(']')[0]
                    # print(type)
                # 文章标题
                title = paper.xpath('./div[@class="clearfix"]/p[@class="art_title"]/a[@class="art_t"]/text()')
                title = ''.join(title).strip()
                # print(title)
                # 是否付费
                fee = paper.xpath(
                    './div[@class="clearfix"]/p[@class="read_article"]/span[@style="padding: 1px 2px;color: #646464; font-size: 12px; border-radius: 3px; border:1px solid #D3D3D3;"]/text()')
                if len(fee) > 0:
                    fee = ''.join(fee).strip()
                else:
                    fee = str('免费')
                # 评价信息
                evaluates = paper.xpath('./div[@class="clearfix"]/p[@class="read_article"]/span[@class="gray1 ml5"]')
                if len(evaluates) == 2:
                    # 好评率
                    good_rate = paper.xpath(
                        './div[@class="clearfix"]/p[@class="read_article"]/span[@class="gray1 ml5"][1]/text()')
                    good_rate = ''.join(good_rate).strip().split('好')[0]
                    # print(good_rate)
                    # 评价量
                    evaluate = paper.xpath(
                        './div[@class="clearfix"]/p[@class="read_article"]/span[@class="gray1 ml5"][2]/text()')
                    evaluate = ''.join(evaluate).strip().split('条')[0]
                    # print(evaluate)
                    # 购买量
                    readings = paper.xpath(
                        './div[@class="clearfix"]/p[@class="read_article"]/span[@class="gray1"][1]/text()')
                    readings = ''.join(readings).strip().split('人')[0]
                    # print(readings)
                    # 发布时间
                    time = paper.xpath(
                        './div[@class="clearfix"]/p[@class="read_article"]/span[@class="gray1"][2]/text()')
                    time = ''.join(time).strip().split('于')[1]
                    # print(time)
                else:
                    good_rate = str('')
                    # print(good_rate)
                    # 评论量
                    evaluate = paper.xpath(
                        './div[@class="clearfix"]/p[@class="read_article"]/span[@class="gray1 ml5"]/text()')
                    evaluate = ''.join(evaluate).strip().split('条')[0]
                    # print(evaluate)
                    # 阅读量
                    readings = paper.xpath(
                        './div[@class="clearfix"]/p[@class="read_article"]/span[@class="gray1"][1]/text()')
                    readings = ''.join(readings).strip().split('人')[0]
                    # print(readings)
                    # 发布时间
                    time = paper.xpath(
                        './div[@class="clearfix"]/p[@class="read_article"]/span[@class="gray1"][2]/text()')
                    time = ''.join(time).strip().split('于')[1]
                    # print(time)
                doctor_papers = []
                doctor_papers.extend([doctor_id, doctor_name, type, title, fee, good_rate, evaluate, readings, time])
                print(doctor_name, '医生科普文章网页的信息：', doctor_papers)
                self.doctor_papers(jibing, doctor_papers)  # -----------------------科普文章网页全部信息-------------


    # 爬取医生在线咨询网站列表url
    def get_zixunweb(self, jibing, allzixun_url, doctor_name):
        # 模拟浏览器访问“在线咨询”的网页
        content = etree.HTML(requests.get(allzixun_url, headers=self.headers).text)
        # sleep(10)

        # 获得在线咨询-分页数量
        page_num = content.xpath('//div[@class="p_bar"]/a[last()-2]/text()')
        if len(page_num) > 0:
            page_num = ''.join(page_num)
            page_num = int(page_num)
            print(doctor_name, '医生共有', str(page_num), '页在线咨询记录')
        else:
            page_num = int(1)
            print(doctor_name, '医生共有', str(page_num), '页在线咨询记录')


        # 如果总页码大于25
        if page_num > 25:
            # 爬取前25页的在线咨询url
            for i in range(1, 26):
                zixunlist_url = allzixun_url + str('?p_type=all&p=') + str(i)
                response = requests.get(zixunlist_url, headers=self.headers)
                # sleep(10)

                print('正在爬取', doctor_name, '第' + str(i) + '页的在线咨询:', zixunlist_url)
                content1 = etree.HTML(response.text)
                zixuns = content1.xpath('//div[@class="zixun_list"]/table/tr')

                for j in range(2, len(zixuns)):
                    zixun = zixuns[j]

                    # 判断咨询时间是否满足条件
                    zixun_time = zixun.xpath('./td[6]/span[@class="gray3"]/text()')
                    zixun_time = ' '.join(zixun_time)
                    # print(zixun_time)

                    # 判断咨询时间是否为本年度(2021年)：5位数
                    if len(zixun_time) == 5:
                        #print(zixun_time)
                        # 判断咨询月份是否满足条件
                        zixun_month = zixun_time.split('.')[0]
                        if '2' in zixun_month: # 爬取咨询月份为2月
                            zixun_url = zixun.xpath('./td[3]/p/a[@class="td_link"]/@href')
                            zixun_url = ''.join(zixun_url).strip()
                            print(zixun_url)
                            f = open('data/' + str(jibing) + '_doctor_zixun_urls', 'a', encoding='utf-8')
                            f.write(zixun_url + '\n')
                            f.close()
                        else:
                            break
                    else:
                        break

        # 如果总页数小于25
        else:
            # 逐页爬取在线咨询url
            for i in range(1, page_num + 1):
                zixunlist_url = allzixun_url + str('?p_type=all&p=') + str(i)
                response = requests.get(zixunlist_url, headers=self.headers)
                # sleep(10)

                print('正在爬取', doctor_name, '第' + str(i) + '页的在线咨询:', zixunlist_url)
                content1 = etree.HTML(response.text)
                zixuns = content1.xpath('//div[@class="zixun_list"]/table/tr')

                for j in range(2, len(zixuns)):
                    zixun = zixuns[j]

                    # 判断咨询时间是否满足条件
                    zixun_time = zixun.xpath('./td[6]/span[@class="gray3"]/text()')
                    zixun_time = ' '.join(zixun_time)
                    # print(zixun_time)

                    # 判断咨询时间是否为本年度(2021年)：5位数
                    if len(zixun_time) == 5:
                        #print(zixun_time)
                        # 判断咨询月份是否满足条件
                        zixun_month = zixun_time.split('.')[0]
                        if '2' in zixun_month: # 爬取咨询月份为2月
                            zixun_url = zixun.xpath('./td[3]/p/a[@class="td_link"]/@href')
                            zixun_url = ''.join(zixun_url).strip()
                            print(zixun_url)
                            f = open('data/' + str(jibing) + '_doctor_zixun_urls', 'a', encoding='utf-8')
                            f.write(zixun_url + '\n')
                            f.close()
                        else:
                            break
                    else:
                        break



    # 爬取医生个人网站统计信息
    def get_selfweb(self, doctor_url, doctor_name, resp):

        try:
            # 模拟浏览器访问“个人网站统计信息”
            content = etree.HTML(resp)
            # sleep(10)
        except Exception as e:
            print("爬虫出错了: " + doctor_url + '  ' + str(e))
            # f = open("data/doctor_list_timeout", "a", encoding="utf-8")
            # f.write(selfurl + '\n')
            # f.close()
        else:
            # 开始对咨询页信息的解析，并存入数据库以及保存咨询页的网页代码
            # etree.HTML()方法用于补全返回网站的结构,便于解析
            # content = etree.HTML(response.text)
            PAGE_DATA = re.search(r'window\.PAGE_DATA = (.*?)<', resp, re.S).group(1)
            keys = re.findall(r'([a-zA-Z0-9]+):', PAGE_DATA)
            for key in keys:
                PAGE_DATA = PAGE_DATA.replace(key, '"' + key + '"')
            page_data = json.loads(PAGE_DATA)
            spaceId = page_data['spaceId']
            toDay = str(datetime.date.today())

            # 总患者
            patients = page_data['allConsultCnt']
            # 总访问量
            total_visits = page_data['doctorHitsCnt']


            hz_url = f'https://qianhaiyandr.haodf.com/ndoctor/ajaxGetDoctorOtherData?startTime={toDay + " 00:00:00"}&endTime={toDay + " 00:00:00"}&spaceId={spaceId}'
            hz_res = requests.get(hz_url, headers=self.headers).json()['data']
            _url = 'https://qianhaiyandr.haodf.com/ndoctor/ajaxGetDoctorData?spaceId=' + spaceId
            _res = requests.get(_url, headers=self.headers).json()['data']
            gift_url = 'https://zhangguobing.haodf.com/ndoctor/ajaxGetCntOfPresent?spaceId=' + spaceId

            # 礼物
            gifts = requests.get(gift_url, headers=self.headers).json()['data']
            # 微信诊后报到患者
            wechat_patients = hz_res[1]
            # 总诊后报到患者
            reported_patients = hz_res[2]
            # 患者投票
            votes = _res['doctorVoteCnt']
            # 感谢信
            letters = _res['thankLetterCount']
            # 开通时间
            opening_time = _res['openSpaceTime']
            # 上次在线
            last_online = _res['spaceActiveDate']
            if '今天' in last_online:
                last_online = datetime.date.today()
            elif '1天前' in last_online:
                last_online = (datetime.date.today() + datetime.timedelta(days=-1))
            elif '2天前' in last_online:
                last_online = (datetime.date.today() + datetime.timedelta(days=-2))
            elif '3天前' in last_online:
                last_online = (datetime.date.today() + datetime.timedelta(days=-3))
            else:
                last_online = last_online
            # 总文章
            articles = content.xpath('/html/body/div[4]/main/section[4]/header/h2/span/span/text()')
            if len(articles) > 0:
                articles = articles[0]
                #print(articles)
            else:
                articles = ''
                #print(articles)
            # 诊后服务星
            star = len(
                content.xpath('//aside[@class="container"][2]/ul[@class="item-body"]/li[1]/span[2]/img[@alt="金色星星"]'))
            star = ''.join(str(star))
            # print(star)
            # 诊治后的患者
            treatmented_patients = content.xpath(
                '//aside[@class="container"][2]/ul[@class="item-body"]/li[2]/span[2]/text()')
            treatmented_patients = ''.join(treatmented_patients).strip().split('例')[0]
            # print(treatmented_patients)
            # 随访中的患者
            treatmenting_patients = content.xpath(
                '//aside[@class="container"][2]/ul[@class="item-body"]/li[3]/span[2]/text()')
            treatmenting_patients = ''.join(treatmenting_patients).strip().split('例')[0]
            # print(treatmenting_patients)

            selfweb_detail = []
            selfweb_detail.extend([letters, gifts, total_visits, articles, patients, wechat_patients, reported_patients,
                                   votes, last_online, opening_time, star, treatmented_patients, treatmenting_patients])
            print(doctor_name, '医生个人网站统计信息：', selfweb_detail)
            return selfweb_detail


    # 将doctor_detail数据保存
    def doctor_detail(self, jibing, data):
        with open(r'data' + str(jibing) + '_doctor_detail.csv',
                  'a+', newline='', encoding='utf-8-sig') as file1:
            mywrite = csv.writer(file1)
            mywrite.writerow(data)


    # 将doctor_visits数据保存
    def doctor_visits(self, jibing, data):
        with open(r'data' + str(jibing) + '_doctor_visits.csv',
                  'a+', newline='', encoding='utf-8-sig') as file2:
            mywrite = csv.writer(file2)
            mywrite.writerow(data)


    # 将doctor_share数据保存
    def doctor_share(self, jibing, data):
        with open(r'data' + str(jibing) + '_doctor_share.csv',
                  'a+', newline='', encoding='utf-8-sig') as file3:
            mywrite = csv.writer(file3)
            mywrite.writerow(data)


    # 将doctor_papers数据保存
    def doctor_papers(self, jibing, data):
        with open(r'data' + str(jibing) + '_doctor_papers.csv',
                  'a+', newline='', encoding='utf-8-sig') as file4:
            mywrite = csv.writer(file4)
            mywrite.writerow(data)


    # 程序开始
    def main(self):
        # 疾病列表
        jibing_list = [.......]
        # 逐个爬取疾病信息
        for jibing in jibing_list:
            print('正在爬取疾病类型：', jibing)
            self.doctor_pageone(jibing)


# 程序入口
if __name__ == '__main__':
    haodf = Haodf()
    haodf.main()
