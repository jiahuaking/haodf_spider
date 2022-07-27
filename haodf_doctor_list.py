import requests
from lxml import etree
from time import *
import csv

headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
}


jibing_list = [.......] # disease type list

for jibing in jibing_list:
    url_begin = 'https://www.haodf.com/jibing/'+ str(jibing) + '/daifu_all_all_all_all_all_'
    print(url_begin)

    # doctor list
    for i in range(1, 68): 
        url = url_begin + str(i) + '.htm'
        response = requests.get(url, headers=headers)

        print('crawling No.'+str(i)+'page',url)
        content = etree.HTML(response.text)
        lists = content.xpath('//li[@class="hp_doc_box_serviceStar"]')
        for j in range(len(lists)):
            list = lists[j]

            doctor_list = []

            name = list.xpath('./div/div[2]/div[@class="oh zoom lh180"]/p[1]/a/text()')
            name = ''.join(name).strip()
            #print(name)

            medical_title = list.xpath('./div/div[2]/div[@class="oh zoom lh180"]/p[1]/span/text()')
            medical_title = ''.join(medical_title).strip()
            #print(medical_title)

            hospital = list.xpath('./div/div[2]/div[@class="oh zoom lh180"]/p[1]/a[2]/span/text()')
            hospital = ''.join(hospital).strip()
            #print(hospital)

            recommend = list.xpath('./div/div[2]/div[@class="oh zoom lh180"]/p[2]/span[1]/a/i/text()')
            recommend = ''.join(recommend).strip()
            #print(recommend)

            url = list.xpath('./div/div[2]/div[@class="fl pr20"]/a/@href')
            url = ''.join(url).strip()

            id = url.replace('https://', '').replace('.haodf.com/', '')
            #print(id)
            #print(url)

            two_votes = list.xpath('./div/div[2]/div[@class="oh zoom lh180"]/p[3]/span/text()')
            two_votes = ''.join(two_votes).strip().split('/')[0].split('票')[1]
            #print(two_votes)

            all_votes = list.xpath('./div/div[2]/div[@class="oh zoom lh180"]/p[3]/span/text()')
            all_votes = ''.join(all_votes).strip().split('/')[1].split('票')[1]
            #print(all_votes)

            respond = list.xpath('./div/div[2]/div[@class="oh zoom lh180"]/p[3]/a/span/text()')
            respond = ''.join(respond).strip()
            #print(respond)

            good_at = list.xpath('./div/div[2]/div[@class="oh zoom lh180"]/p[4]/text()')
            good_at = ''.join(good_at).strip().split('：')[1]
            #print(good_at)
            doctor_list.extend([id, name, medical_title, hospital, recommend, url, two_votes, all_votes, respond, good_at])

            prices = list.xpath('./div/div[2]/div[@class="oh zoom lh180"]/p[@class="product-type"]/span[@class="pt-item"]/text()')
            #print(prices)
            for price in prices:
                price = ''.join(price).strip()
                #print(price)
                doctor_list.extend([price])

            #print(doctor_lists)
            print('No.'+str(i)+'page information:',doctor_list)
            with open(r'data'+str(jibing)+'_doctor_list.csv','a+', newline='',encoding='utf-8') as f1:
                writer = csv.writer(f1)
                writer.writerow(doctor_list)

        doctor_urls = content.xpath('//div[@class="fl pr20"]/a/@href')
        print('No.'+str(i)+'page url: ', doctor_urls)
        for doctor_url in doctor_urls:
            f = open('data/'+ str(jibing) + '_doctor_urls', 'a', encoding='utf-8')
            f.write(doctor_url + '\n')
            f.close()
        sleep(1)


