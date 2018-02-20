import requests
import json
import math
import copy

from bs4 import BeautifulSoup
from auchan_request_template import JSON_template

novus_template_url = {'beer': 'https://novus.zakaz.ua/uk/beer/?&page={}',
                      'vodka': 'https://novus.zakaz.ua/uk/vodka/?&page={}',
                      'wine': 'https://novus.zakaz.ua/uk/wine/?&page={}',
                      'champagne': 'https://novus.zakaz.ua/uk/champagne-sparkling-wine/?&page={}',
                      'cognac': 'https://novus.zakaz.ua/uk/cognac/?&page={}'}
novus_dict = {}

mm_dict = {'beer': 'https://megamarket.ua/ua/catalogue/category/1090?show=48000',
           'vodka': 'https://megamarket.ua/ua/catalogue/category/1050?show=48000',
           'wine': 'https://megamarket.ua/ua/catalogue/category/1040?show=48000',
           'champagne':'https://megamarket.ua/ua/catalogue/category/1110?show=48000',
           'cognac':'https://megamarket.ua/ua/catalogue/category/1070?show=48000'}

auchan_gen = {'beer': 'beer',
               'vodka': 'vodka',
               'wine': 'wine',
               'champagne': 'champagne-sparkling-wine',
               'cognac': 'cognac'}
auchan_dict = {}


def auchan_generate_url():
    api_url = 'https://auchan.zakaz.ua/api/query.json'
    json_template = JSON_template.copy()
    for category_name in auchan_gen:
        json_template['request'][0]['args']['slugs'][0] = auchan_gen[category_name]
        json_data = requests.post(api_url, json=json_template).text
        products_count = json.loads(json_data)['responses'][0]['data']['items'][0]['facets_base']['total']
        pages_count = math.ceil(products_count/50)
        json_request_list = []
        for page_num in range(1, int(pages_count+1)):
            json_template['request'][0]['offset'] = page_num
            json_request_list.append(copy.deepcopy(json_template))

        one_category_dict = {category_name: json_request_list}
        auchan_dict.update(one_category_dict)


def novus_generate_url():
    for x in novus_template_url.keys():
        html_code = requests.get(novus_template_url[x].format(1)).text
        soup = BeautifulSoup(html_code, 'lxml')
        number_max_page = soup.find('div', class_='pagination pagination-centered')
        number_max_page = int(number_max_page.find_all('a')[-2].text)
        urls = []
        for y in range(1, number_max_page+1):
            urls.append(novus_template_url[x].format(y))
        novus_dict.update({x: urls})


auchan_generate_url()
novus_generate_url()
