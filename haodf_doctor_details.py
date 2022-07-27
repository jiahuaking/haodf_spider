import csv
import datetime
import os
from time import *
import json
import re
import requests
from lxml import etree


class Haodf():
    # initializing the browser
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
        }

    # get the urls of six websites
    def doctor_pageone(self, jibing):
        
        rootDir = "data" + str(jibing) + "_doctor_html"
        finished = []  # list of doctors who have gotten
        for parent, dirnames, filenames in os.walk(rootDir):
            for filename in filenames:
                finished.append(filename)

        # read urls line by line
        f = open('data/' + str(jibing) + '_doctor_urls', 'r', encoding='utf-8')
        while True:
  
            line = f.readline()
            if not line:
                break

            # judge if the doctor has gotten
            url = line.replace('\n', '')
            finished_id = url.replace('https://', '').replace('.haodf.com/', '')
            if finished_id in finished:
                print('the doctor has gotten')
                continue
            print('------', url, '------')

            # store doctor information
            doctor_detail = []
            doctor_id = url.replace('https://', '').replace('.haodf.com/', '')
            doctor_detail.append(doctor_id)

            if self.headers.get('Cookie'):
                del self.headers['Cookie']
            _resp = requests.get(url, headers=self.headers)
            resp = _resp.text
            self.headers['Cookie'] = '__jsluid_s=' + _resp.cookies.get('__jsluid_s')
            content = etree.HTML(resp)
            beginweb_detail = self.parse_beginweb(content)
            doctor_detail.extend(beginweb_detail)

            doctor_name = beginweb_detail[0]

            doctor_url = ''.join(url).strip()
            if len(doctor_url) > 0:
                print('crawling ', doctor_name, doctor_url)
                selfweb_detail = self.get_selfweb(doctor_url, doctor_name, resp)
                doctor_detail.extend(selfweb_detail)
            else:
                selfweb_detail = [''] * 13
                doctor_detail.extend(selfweb_detail)
                print(doctor_name, 'who does not have homepage')

            # url of appointment
            appointment_url = content.xpath(
                '//div[@class="container service-outer"]/ul[@class="clearfix"]/li[3]/a/@href')
            if len(appointment_url) > 0:
                appointment_url = ''.join(appointment_url).strip()
                print('crawling ', doctor_name, appointment_url)
                appointment_detail = self.get_appointmentweb(appointment_url, doctor_name)
                doctor_detail.extend(appointment_detail)
            else:
                appointment_detail = ['']
                doctor_detail.extend(appointment_detail)
                print(doctor_name, 'who does not have appointment')

            print(doctor_name, '：', doctor_detail)
            self.doctor_detail(jibing, doctor_detail)  

            # url of allvisit
            allvisit_url = content.xpath('//section[@class="container"][1]/header/h2/a/@href')
            if len(allvisit_url) > 0:
                allvisit_url = ''.join(allvisit_url).strip()
                print('crawling ', doctor_name, allvisit_url)
                self.get_visitweb(jibing, allvisit_url, doctor_id, doctor_name)
            else:
                print(doctor_name, 'who does not have allvisit')

            # url of allshare
            allshare_url = content.xpath('//section[@class="container"][2]/header/a/@href')
            print('crawling ', doctor_name, allshare_url)
            if len(allshare_url) > 0:
                self.get_shareweb(jibing, allshare_url, doctor_id, doctor_name)

            # url of allpaper
            allpaper_url = content.xpath('//section[@class="container"]/header/h2/a[@href="/lanmu"]/@href')
            if len(allpaper_url) > 0:
                allpaper_url = str(url) + str(allpaper_url[0])
                print('crawling ', doctor_name, allpaper_url)
                self.get_paperweb(jibing, allpaper_url, doctor_id, doctor_name)
            else:
                print(doctor_name, 'who does not have allpaper')

            # url of allzixun
            allzixun_url = content.xpath('//section[@class="container"]/header/h2/a[@href="/zixun/list.htm"]/@href')
            if len(allzixun_url) > 0:
                allzixun_url = str(url) + str(allzixun_url[0])
                print('crawling ', doctor_name, allzixun_url)
                self.get_zixunweb(jibing, allzixun_url, doctor_name)


            self.finished(jibing, finished_id, content)

        f.close()


    def finished(self, jibing, finished_id, content):
        doctor_detail_html = etree.tostring(content).decode('utf-8')
        f = open("data" + str(jibing) + "_doctor_html/" + finished_id, "w", encoding = "utf-8")
        f.write(doctor_detail_html)
        f.close()


    # parse information in the doctor homepage
    def parse_beginweb(self, content): 

        name = content.xpath('//div[@class="profile-txt"]/h1[@class="doctor-name"]/text()')
        name = ''.join(name).strip()
        # print(name)

        department = content.xpath('//div[@class="profile-txt"]/ul/li[@class="doctor-faculty"]/a[1]/text()')
        department = ''.join(department).strip()
        # print(department)

        medical_title = content.xpath('//div[@class="profile-txt"]/span[@class="doctor-title"]/text()')
        medical_title = ''.join(medical_title)
        # print(medical_title)
 
        academic_title = content.xpath('//div[@class="profile-txt"]/span[@class="doctor-educate-title"]/text()')
        academic_title = ''.join(academic_title).strip()
        # print(academic_title)

        good_at = content.xpath('//div[@class="brief-container"]/div[@class="clearfix"][1]/div/p/text()')
        good_at = ''.join(good_at).strip().replace('\n', '')
        # print(good_at)

        job = content.xpath('//div[@class="brief-container"]/div[@class="clearfix"][2]/div/p/text()')
        job = ''.join(job).strip().replace('\n', '')
        # print(job)

        recommend = content.xpath('//ul[@class="profile-statistic"]/li[1]/span[@class="value"]/text()')
        recommend = ''.join(recommend).strip()
        # print(recommend)

        services = content.xpath(
            '//div[@class="container service-outer"]/ul[@class="clearfix"]/li[@class="service-item"]/a/text()')
        services = ''.join(services).strip().replace('\n                    ', '/').replace('//    ', '/').replace('//    ', '/')
        # print(services)

        efficacy_satisfaction = content.xpath('//div[@class="satisfaction clearfix"]/div[1]/i/text()')
        efficacy_satisfaction = ''.join(efficacy_satisfaction).strip()
        # print(efficacy_satisfaction)

        attitude_satisfaction = content.xpath('//div[@class="satisfaction clearfix"]/div[2]/i/text()')
        attitude_satisfaction = ''.join(attitude_satisfaction).strip()
        # print(attitude_satisfaction)

        beginweb_detail = []
        beginweb_detail.extend([name, department, medical_title, academic_title, good_at, job, recommend, services,
                                efficacy_satisfaction, attitude_satisfaction])
        print(name, '：', beginweb_detail)
        return beginweb_detail


    # get information in the appointment website
    def get_appointmentweb(self, appointment_url, doctor_name):

        content = etree.HTML(requests.get(appointment_url, headers=self.headers).text)
        # sleep(1)

        appointments = content.xpath(
            '//ul[@class="r-c-list"]/li[@class="r-c-item clearfix"]/div[@class="r-c-i-info"]/p[@class="r-c-i-count"]')
        appointment_detail = []
        for i in range(len(appointments)):
            appointment = appointments[i]


            referrals = appointment.xpath('./span/text()')
            referrals = ''.join(referrals).strip()
            # print(referrals)

            appointment_detail.extend([referrals])
        print(doctor_name, '：', appointment_detail)
        return appointment_detail


    # get information in the allvisit website
    def get_visitweb(self, jibing, allvisit_url, doctor_id, doctor_name):

        content = etree.HTML(requests.get(allvisit_url, headers=self.headers).text)
        # sleep(10)

        visits = content.xpath('//li[@class="menzhen-ul-li"]')
        for i in range(len(visits)):
            visit = visits[i]

            date = visit.xpath('./div[@class="time"]/p[1]/text()')
            date = ''.join(date).strip()
            # print(date)

            week = visit.xpath('./div[@class="time"]/p[2]/text()')
            week = ''.join(week).strip()
            # print(week)

            hospital = visit.xpath('./div[@class="info"]/ul/li[1]/h2/text()')
            hospital = ''.join(hospital).strip()
            # print(hospital)

            location = visit.xpath('./div[@class="info"]/ul/li[1]/h2/a/text()')
            location = ''.join(location).strip()
            # print(location)

            department = visit.xpath('./div[@class="info"]/ul/li[2]/p[2]/text()')
            department = ''.join(department).strip()
            # print(department)

            type = visit.xpath('./div[@class="info"]/ul/li[3]/p[2]/text()')
            type = ''.join(type).strip()
            # print(type)

            doctor_visits = []
            doctor_visits.extend([doctor_id, doctor_name, date, week, hospital, location, department, type])
            print(doctor_name, '：', doctor_visits)
            self.doctor_visits(jibing, doctor_visits) 


    # get information in the allshare website
    def get_shareweb(self, jibing, allshare_url, doctor_id, doctor_name):

        allshare_url = ''.join(allshare_url).strip()

        content = etree.HTML(requests.get(allshare_url, headers=self.headers).text)

        page_num = content.xpath('//a[@class="p_text"]/text()')
        if len(page_num) > 0:
            page_num = ''.join(page_num).strip().split('共')[1].split('页')[0]
            page_num = int(page_num)

        else:
            page_num = int(1)


        for i in range(1, page_num + 1):
            url = allshare_url.split('.htm')[0]
            url = url + '/' + str(i) + '.htm'
            response = requests.get(url, headers=self.headers)
            # sleep(10)

            content1 = etree.HTML(response.text)
            tables = content1.xpath('//div[@class ="item-body"]/div[@class="patient-eva"]')
            for j in range(len(tables)):
                table = tables[j]


                date = table.xpath('./div[@class="eva-footer clearfix"]/div[@class="evaluate-date"]/text()')
                date = ''.join(date).strip()
                if '今天' in date:
                    date = datetime.date.today()
                else:
                    date = date

                patient_name = table.xpath('./div[@class="patient-eva-header"]/span[1]/text()')
                patient_name = ''.join(patient_name).strip().split('：')[1]
                # print(patient_name)

                disease = table.xpath('./div[@class="patient-eva-header"]/a/span/text()')
                disease = ''.join(disease).strip()
                # print(disease)

                aim = table.xpath('./div[@class="clearfix"]/span[1]/text()')
                aim = ''.join(aim).strip().split('：')[1]
                # print(aim)

                way = table.xpath('./div[@class="clearfix"]/span[2]/text()')
                way = ''.join(way).strip().split('：')[1]
                # print(way)

                effect = table.xpath('./div[@class="clearfix"]/span[3]/text()')
                if len(effect) == 0:
                    effect = 'no filled'
                else:
                    effect = ''.join(effect).strip()
                # print(effect)

                attitude = table.xpath('./div[@class="clearfix"]/span[4]/text()')
                if len(effect) == 0:
                    attitude = 'no filled'
                else:
                    attitude = ''.join(attitude).strip()
                # print(attitude)

                fee = table.xpath('./div[@class="clearfix"]/span[5]/text()')
                fee = ''.join(fee).strip()
                # print(fee)

                state = table.xpath('./div[@class="clearfix"]/span[6]/text()')
                state = ''.join(state).strip()
                # print(state)

                reason = table.xpath('./div[@class="clearfix"]/span[7]/text()')
                reason = ''.join(reason).strip()
                # print(reason)

                tag = table.xpath('./div[@class="trait-bd"]/div[@class="trait"]/text()')
                tag = '/'.join(tag).strip()
                # print(tag)

                experience_thank = table.xpath('./div[@class="eva-detail"]/text()')
                experience_thank = ''.join(experience_thank).strip().replace(' ', '')
                # print(experience_thank)

                doctor_share = []
                doctor_share.extend(
                    [doctor_id, doctor_name, patient_name, disease, aim, way, effect, attitude, tag, experience_thank,
                     date, reason, state, fee])
                print(doctor_name, '：', doctor_share)
                self.doctor_share(jibing, doctor_share)  


    # get information in the allpaper website
    def get_paperweb(self, jibing, allpaper_url, doctor_id, doctor_name):

        content = etree.HTML(requests.get(allpaper_url, headers=self.headers).text)
        # sleep(10)

        page_num = content.xpath(
            '//div[@class="page_main"]/div[@class="page_turn"]/a[@class="page_turn_a" and @rel="true"]/text()')
        if len(page_num) > 0:
            page_num = ''.join(page_num).strip().split('共')[1].split('页')[0]
            page_num = int(page_num)

        else:
            page_num = int(1)
            

        for i in range(1, page_num + 1):
            paper_url = allpaper_url + str('_') + str(i)
            response = requests.get(paper_url, headers=self.headers)
            # sleep(10)

            content1 = etree.HTML(response.text)
            papers = content1.xpath('//ul[@class="article_ul"]/li')

            for j in range(len(papers)):
                paper = papers[j]

                type = paper.xpath('./div[@class="clearfix"]/p[@class="art_title"]/font/text()')

                if len(type) == 0:
                    type = paper.xpath('./div[@class="clearfix"]/p[@class="art_title"]/a[1]/text()')
                    type = ''.join(type).strip().split('[')[1].split(' ')[0]
                    # print(type)

                else:
                    type = type
                    type = ''.join(type).strip().split('[')[1].split(']')[0]
                    # print(type)

                title = paper.xpath('./div[@class="clearfix"]/p[@class="art_title"]/a[@class="art_t"]/text()')
                title = ''.join(title).strip()
                # print(title)

                fee = paper.xpath(
                    './div[@class="clearfix"]/p[@class="read_article"]/span[@style="padding: 1px 2px;color: #646464; font-size: 12px; border-radius: 3px; border:1px solid #D3D3D3;"]/text()')
                if len(fee) > 0:
                    fee = ''.join(fee).strip()
                else:
                    fee = str('free')

                evaluates = paper.xpath('./div[@class="clearfix"]/p[@class="read_article"]/span[@class="gray1 ml5"]')
                if len(evaluates) == 2:

                    good_rate = paper.xpath(
                        './div[@class="clearfix"]/p[@class="read_article"]/span[@class="gray1 ml5"][1]/text()')
                    good_rate = ''.join(good_rate).strip().split('好')[0]
                    # print(good_rate)

                    evaluate = paper.xpath(
                        './div[@class="clearfix"]/p[@class="read_article"]/span[@class="gray1 ml5"][2]/text()')
                    evaluate = ''.join(evaluate).strip().split('条')[0]
                    # print(evaluate)

                    readings = paper.xpath(
                        './div[@class="clearfix"]/p[@class="read_article"]/span[@class="gray1"][1]/text()')
                    readings = ''.join(readings).strip().split('人')[0]
                    # print(readings)

                    time = paper.xpath(
                        './div[@class="clearfix"]/p[@class="read_article"]/span[@class="gray1"][2]/text()')
                    time = ''.join(time).strip().split('于')[1]
                    # print(time)
                else:
                    good_rate = str('')
                    # print(good_rate)

                    evaluate = paper.xpath(
                        './div[@class="clearfix"]/p[@class="read_article"]/span[@class="gray1 ml5"]/text()')
                    evaluate = ''.join(evaluate).strip().split('条')[0]
                    # print(evaluate)

                    readings = paper.xpath(
                        './div[@class="clearfix"]/p[@class="read_article"]/span[@class="gray1"][1]/text()')
                    readings = ''.join(readings).strip().split('人')[0]
                    # print(readings)

                    time = paper.xpath(
                        './div[@class="clearfix"]/p[@class="read_article"]/span[@class="gray1"][2]/text()')
                    time = ''.join(time).strip().split('于')[1]
                    # print(time)
                doctor_papers = []
                doctor_papers.extend([doctor_id, doctor_name, type, title, fee, good_rate, evaluate, readings, time])
                print(doctor_name, '：', doctor_papers)
                self.doctor_papers(jibing, doctor_papers) 


    # get information in the allzixun website
    def get_zixunweb(self, jibing, allzixun_url, doctor_name):

        content = etree.HTML(requests.get(allzixun_url, headers=self.headers).text)
        # sleep(10)

        page_num = content.xpath('//div[@class="p_bar"]/a[last()-2]/text()')
        if len(page_num) > 0:
            page_num = ''.join(page_num)
            page_num = int(page_num)

        else:
            page_num = int(1)

        if page_num > 25:

            for i in range(1, 26):
                zixunlist_url = allzixun_url + str('?p_type=all&p=') + str(i)
                response = requests.get(zixunlist_url, headers=self.headers)
                # sleep(10)

                print('crawling ', doctor_name, 'No.' + str(i) + 'page:', zixunlist_url)
                content1 = etree.HTML(response.text)
                zixuns = content1.xpath('//div[@class="zixun_list"]/table/tr')

                for j in range(2, len(zixuns)):
                    zixun = zixuns[j]

                    zixun_time = zixun.xpath('./td[6]/span[@class="gray3"]/text()')
                    zixun_time = ' '.join(zixun_time)
                    # print(zixun_time)


                    if len(zixun_time) == 5:
                        #print(zixun_time)

                        zixun_month = zixun_time.split('.')[0]
                        if '2' in zixun_month:
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


        else:

            for i in range(1, page_num + 1):
                zixunlist_url = allzixun_url + str('?p_type=all&p=') + str(i)
                response = requests.get(zixunlist_url, headers=self.headers)
                # sleep(10)

                content1 = etree.HTML(response.text)
                zixuns = content1.xpath('//div[@class="zixun_list"]/table/tr')

                for j in range(2, len(zixuns)):
                    zixun = zixuns[j]

                    zixun_time = zixun.xpath('./td[6]/span[@class="gray3"]/text()')
                    zixun_time = ' '.join(zixun_time)
                    # print(zixun_time)

                    if len(zixun_time) == 5:
                        #print(zixun_time)

                        zixun_month = zixun_time.split('.')[0]
                        if '2' in zixun_month: 
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



    # get information in the doctor homepage
    def get_selfweb(self, doctor_url, doctor_name, resp):

        try:
            content = etree.HTML(resp)
            # sleep(10)
        except Exception as e:
            print("has a error: " + doctor_url + '  ' + str(e))
            # f = open("data/doctor_list_timeout", "a", encoding="utf-8")
            # f.write(selfurl + '\n')
            # f.close()
        else:
            
            # content = etree.HTML(response.text)
            PAGE_DATA = re.search(r'window\.PAGE_DATA = (.*?)<', resp, re.S).group(1)
            keys = re.findall(r'([a-zA-Z0-9]+):', PAGE_DATA)
            for key in keys:
                PAGE_DATA = PAGE_DATA.replace(key, '"' + key + '"')
            page_data = json.loads(PAGE_DATA)
            spaceId = page_data['spaceId']
            toDay = str(datetime.date.today())

            patients = page_data['allConsultCnt']

            total_visits = page_data['doctorHitsCnt']


            hz_url = f'https://qianhaiyandr.haodf.com/ndoctor/ajaxGetDoctorOtherData?startTime={toDay + " 00:00:00"}&endTime={toDay + " 00:00:00"}&spaceId={spaceId}'
            hz_res = requests.get(hz_url, headers=self.headers).json()['data']
            _url = 'https://qianhaiyandr.haodf.com/ndoctor/ajaxGetDoctorData?spaceId=' + spaceId
            _res = requests.get(_url, headers=self.headers).json()['data']
            gift_url = 'https://zhangguobing.haodf.com/ndoctor/ajaxGetCntOfPresent?spaceId=' + spaceId


            gifts = requests.get(gift_url, headers=self.headers).json()['data']

            wechat_patients = hz_res[1]

            reported_patients = hz_res[2]

            votes = _res['doctorVoteCnt']

            letters = _res['thankLetterCount']

            opening_time = _res['openSpaceTime']

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

            articles = content.xpath('/html/body/div[4]/main/section[4]/header/h2/span/span/text()')
            if len(articles) > 0:
                articles = articles[0]
                #print(articles)
            else:
                articles = ''
                #print(articles)

            star = len(
                content.xpath('//aside[@class="container"][2]/ul[@class="item-body"]/li[1]/span[2]/img[@alt="金色星星"]'))
            star = ''.join(str(star))
            # print(star)

            treatmented_patients = content.xpath(
                '//aside[@class="container"][2]/ul[@class="item-body"]/li[2]/span[2]/text()')
            treatmented_patients = ''.join(treatmented_patients).strip().split('例')[0]
            # print(treatmented_patients)

            treatmenting_patients = content.xpath(
                '//aside[@class="container"][2]/ul[@class="item-body"]/li[3]/span[2]/text()')
            treatmenting_patients = ''.join(treatmenting_patients).strip().split('例')[0]
            # print(treatmenting_patients)

            selfweb_detail = []
            selfweb_detail.extend([letters, gifts, total_visits, articles, patients, wechat_patients, reported_patients,
                                   votes, last_online, opening_time, star, treatmented_patients, treatmenting_patients])
            print(doctor_name, '：', selfweb_detail)
            return selfweb_detail



    def doctor_detail(self, jibing, data):
        with open(r'data' + str(jibing) + '_doctor_detail.csv',
                  'a+', newline='', encoding='utf-8-sig') as file1:
            mywrite = csv.writer(file1)
            mywrite.writerow(data)



    def doctor_visits(self, jibing, data):
        with open(r'data' + str(jibing) + '_doctor_visits.csv',
                  'a+', newline='', encoding='utf-8-sig') as file2:
            mywrite = csv.writer(file2)
            mywrite.writerow(data)



    def doctor_share(self, jibing, data):
        with open(r'data' + str(jibing) + '_doctor_share.csv',
                  'a+', newline='', encoding='utf-8-sig') as file3:
            mywrite = csv.writer(file3)
            mywrite.writerow(data)



    def doctor_papers(self, jibing, data):
        with open(r'data' + str(jibing) + '_doctor_papers.csv',
                  'a+', newline='', encoding='utf-8-sig') as file4:
            mywrite = csv.writer(file4)
            mywrite.writerow(data)



    def main(self):

        jibing_list = [.......] # disease type list

        for jibing in jibing_list:
            print('disease type：', jibing)
            self.doctor_pageone(jibing)



if __name__ == '__main__':
    haodf = Haodf()
    haodf.main()
