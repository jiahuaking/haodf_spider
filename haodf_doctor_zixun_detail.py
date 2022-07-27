from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
import datetime
import time
import csv
import os

driver = webdriver.Chrome()
wait = WebDriverWait(driver, 10)


def get_zixun_detail(jibing):

    rootDir = "data" + str(jibing) + "_doctor_zixun_html"
    finished = []  
    for parent, dirnames, filenames in os.walk(rootDir):
        for filename in filenames:
            finished.append(filename)

    f = open("data/" + str(jibing) + "_doctor_zixun_urls", "r", encoding="utf-8")
    while True:
 
        line = f.readline()
        if not line:
            break


        url = line.replace('\n', '')
        finished_id = url.replace('https://www.haodf.com/kanbing/', '').replace('.html', '')
        if finished_id in finished:
            print('~~~have gotten~~~')
            continue
        print('------', url, '------')

        try:
            driver.get(url)
            time.sleep(3)

 
            first_page = driver.page_source
            zixun_first = pq(first_page)

            doctor_name = zixun_first.find('.info-text-name').text()
            doctor_name = ''.join(doctor_name).strip()
            #print(doctor_name)

            doctor_id = zixun_first.find('.card-info-text a').attr('href')
            doctor_id = ''.join(doctor_id).strip().replace('https://', '').replace('.haodf.com', '')
            #print(doctor_id)

            patient_name = zixun_first.find('.header-content div').text()
            patient_name = ''.join(patient_name).strip().split(' ')[0]
            #print(patient_name)

            patient_sex = zixun_first.find('.header-content div').text()
            patient_sex = ''.join(patient_sex).strip().split(' ')[1]
            #print(patient_sex)

            zixundate = zixun_first.find('.info-time').text()
            zixundate = ''.join(zixundate).strip().split(' ')[0]
            #print(zixundate)

            first_time= zixun_first.find('.header-info').text()
            first_time = ''.join(first_time).strip().split(' ')[3]
            #print(first_time)

            times = zixun_first.find('.header-info').text()
            times = ''.join(times).strip().split(' ')[4].split('共')[1].split('次')[0]
            #print(times)

            title = zixun_first.find('.header-content h1').text()
            title = ''.join(title).strip()
            #print(title)

            servicetype = zixun_first.find('.bccard-title').text()
            servicetype = ''.join(servicetype).strip().split('了')[1].split('服')[0]
            #print(servicetype)


            items = zixun_first.find('.diseaseinfo div div').items()
            diseaseinfo = []
            for item in items:

                infotitle = item.find('.info3-title').text()
                #print(infotitle)

                infocontent = item.find('.info3-value p').text()
                #print(infocontent)
                info = str(infotitle).split('\n')[0] + str(infocontent).split('\n')[0]
                #print(info)
                diseaseinfo.extend([info])

            first_page_detail =[]
            first_page_detail.extend([doctor_name, doctor_id, patient_name, patient_sex, zixundate, first_time, times,
                                      title, servicetype, diseaseinfo])

            zixun_detail = []
            zixun_detail.extend(first_page_detail)


            zixun_url = zixun_first.find('.bccard a').attr('href')
            zixun_url = ''.join(zixun_url).strip()

            get_zixunweb(zixun_url, zixun_detail)


            save_zixun_detail(zixun_detail, jibing)


            save_finished(finished_id, jibing)

        except Exception as e:
            print(e.args)

    f.close()
    driver.close()


def save_finished(finished_id, jibing):
    f = open("data" + str(jibing) + "_doctor_zixun_html/" + finished_id, "w", encoding = "utf-8")
    f.close()


def get_zixunweb(zixun_url, zixun_detail):
    driver.get(zixun_url)

    try:

        more = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'msg-more-link-text'))
        )
        #print(len(more.text))
        while len(more.text) > 0:
            js = 'document.querySelector("#app > section.left-heart > section > section.msgboard.js-msgboard > div.msg-more >' \
                 ' div.msg-more-link.js-msg-more-link > span").click()'
            driver.execute_script(js)
            time.sleep(3)

        parse_zixun_web(zixun_url, zixun_detail)
    except TimeoutError:
        get_zixunweb(zixun_url, zixun_detail)


def parse_zixun_web(zixun_url, zixun_detail):
    print('crawling ', zixun_url)
    zixun_web = driver.page_source
    doc = pq(zixun_web)

    zixun_page_detail = []

    items = doc('#msgboard > div > div.msg-item').items()
    for item in items:

        time = item.find('.msg-time').text()
        time = ''.join(time).strip()
        if '今天' in time:
            time = datetime.date.today()
        elif '昨天' in time:
            time = (datetime.date.today() + datetime.timedelta(days=-1))
        else:
            time = time
        #print(time)

        name = item.find('.content-name').text()
        name = ''.join(name).strip().split(' ')[0]
        #print(name)
        content = item.find('.content-him').text()
        content = ''.join(content).strip()
        #print(content)
        interaction = str(time) + str('; ') + str(name) + str('; ') + str(content)
        #print(interaction)
        detail = []
        detail.extend([interaction])

        zixun_page_detail.extend(detail)
        zixun_detail.extend(zixun_page_detail)
    print(zixun_detail)
    return zixun_detail


def save_zixun_detail(zixun_detail, jibing):
    with open (r'data' + str(jibing) + '_doctor_zixun_detail.csv', 'a+', newline = '', encoding = 'utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(zixun_detail)
        time.sleep(3)


def main():

    jibing_list = [...] # disease type

    for jibing in jibing_list:
        print(jibing)
        get_zixun_detail(jibing)


if __name__ == '__main__':
    main()
