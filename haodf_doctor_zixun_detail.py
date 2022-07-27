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
    # 爬取开始之前，先做是否爬取过的判断，取出已爬取在线咨询的列表
    rootDir = "data" + str(jibing) + "_doctor_zixun_html"
    finished = []  # 已经完成列表
    for parent, dirnames, filenames in os.walk(rootDir):
        for filename in filenames:
            finished.append(filename)

    f = open("data/" + str(jibing) + "_doctor_zixun_urls", "r", encoding="utf-8")
    while True:
        # 若读取到文件最尾端，跳出循环，结束爬虫
        line = f.readline()
        if not line:
            break

        # 判断该在线咨询是否爬取过，若爬取过，则跳出此次循环，进入下一个条
        url = line.replace('\n', '')
        finished_id = url.replace('https://www.haodf.com/kanbing/', '').replace('.html', '')
        if finished_id in finished:
            print('该在线咨询已经爬取过~')
            continue
        print('------', url, '------')

        try:
            driver.get(url)
            time.sleep(3)

            # 等待在线咨询首页加载
            first_page = driver.page_source
            zixun_first = pq(first_page)
            # 首页医生信息
            # 医生姓名
            doctor_name = zixun_first.find('.info-text-name').text()
            doctor_name = ''.join(doctor_name).strip()
            #print(doctor_name)
            # 医生id
            doctor_id = zixun_first.find('.card-info-text a').attr('href')
            doctor_id = ''.join(doctor_id).strip().replace('https://', '').replace('.haodf.com', '')
            #print(doctor_id)
            # 患者姓名
            patient_name = zixun_first.find('.header-content div').text()
            patient_name = ''.join(patient_name).strip().split(' ')[0]
            #print(patient_name)
            # 患者性别
            patient_sex = zixun_first.find('.header-content div').text()
            patient_sex = ''.join(patient_sex).strip().split(' ')[1]
            #print(patient_sex)
            # 咨询日期
            zixundate = zixun_first.find('.info-time').text()
            zixundate = ''.join(zixundate).strip().split(' ')[0]
            #print(zixundate)
            # 是否为首诊
            first_time= zixun_first.find('.header-info').text()
            first_time = ''.join(first_time).strip().split(' ')[3]
            #print(first_time)
            # 诊疗次数
            times = zixun_first.find('.header-info').text()
            times = ''.join(times).strip().split(' ')[4].split('共')[1].split('次')[0]
            #print(times)
            # 标题
            title = zixun_first.find('.header-content h1').text()
            title = ''.join(title).strip()
            #print(title)
            # 服务类型
            servicetype = zixun_first.find('.bccard-title').text()
            servicetype = ''.join(servicetype).strip().split('了')[1].split('服')[0]
            #print(servicetype)

            # 疾病信息
            items = zixun_first.find('.diseaseinfo div div').items()
            diseaseinfo = []
            for item in items:
                # 标题
                infotitle = item.find('.info3-title').text()
                #print(infotitle)
                # 内容
                infocontent = item.find('.info3-value p').text()
                #print(infocontent)
                info = str(infotitle).split('\n')[0] + str(infocontent).split('\n')[0]
                #print(info)
                diseaseinfo.extend([info])

            first_page_detail =[]
            first_page_detail.extend([doctor_name, doctor_id, patient_name, patient_sex, zixundate, first_time, times,
                                      title, servicetype, diseaseinfo])
            #print('该在线咨询首页信息为', first_page_detail)

            zixun_detail = []
            zixun_detail.extend(first_page_detail)

            # 查看本次诊疗详情
            zixun_url = zixun_first.find('.bccard a').attr('href')
            zixun_url = ''.join(zixun_url).strip()
            #print('该诊疗详情页url为', zixun_url)
            get_zixunweb(zixun_url, zixun_detail)

            # 保存在线咨询的所有内容
            save_zixun_detail(zixun_detail, jibing)

            # 保存已爬取咨询id
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

    #print('获取该在线咨询详情页', zixun_url)
    try:
        # 查看是否存在“查看更多交流”
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
    print('爬取该在线咨询详情页', zixun_url, '内容')
    zixun_web = driver.page_source
    doc = pq(zixun_web)

    zixun_page_detail = []

    # 医患交互内容
    items = doc('#msgboard > div > div.msg-item').items()
    for item in items:
        # 时间
        time = item.find('.msg-time').text()
        time = ''.join(time).strip()
        if '今天' in time:
            time = datetime.date.today()
        elif '昨天' in time:
            time = (datetime.date.today() + datetime.timedelta(days=-1))
        else:
            time = time
        #print(time)
        # 内容
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
    print('该在线咨询内容：', zixun_detail)
    return zixun_detail


def save_zixun_detail(zixun_detail, jibing):
    with open (r'data' + str(jibing) + '_doctor_zixun_detail.csv', 'a+', newline = '', encoding = 'utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(zixun_detail)
        time.sleep(3)


def main():
    # 疾病列表
    jibing_list = ['yanyan']
    # 逐个爬取疾病信息
    for jibing in jibing_list:
        print('正在爬取疾病类型：',jibing)
        get_zixun_detail(jibing)


if __name__ == '__main__':
    main()









