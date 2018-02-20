import requests

from bs4 import BeautifulSoup

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


novus_generate_url()
