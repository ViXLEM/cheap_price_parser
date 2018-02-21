import grequests
import json
import time
import requests
import math
import copy

from bs4 import BeautifulSoup
from models import Session
from models import AuchanProduct, NovusProduct, MMProduct, Product
from auchan_request_template import JSON_template


class Supermarket():
    def __init__(self, orm, name):
        self.metadata = {'products_count': '', 'new_products_count': '',
                         'download_time': '', 'save_to_db_time': '', 'merge_time': ''}
        self.supermarket_orm = orm
        self.supermarket_name = name
        self.new_goods_barcode = []
        self.generate_url()

    def save_to_db(self):
        """This func save dict goods to personal db."""

        session = Session()

        for x in session.query(self.supermarket_orm).all():  # deactivate all products
            x.active = False
        session.commit()

        for barcode in self.goods_dict:
            product = session.query(self.supermarket_orm).filter_by(barcode=barcode).first()

            if product:
                product.price = self.goods_dict[barcode]['price']
                product.active = True
                continue
            self.new_goods_barcode.append(barcode)
            product = self.supermarket_orm(barcode=barcode,
                                           name=self.goods_dict[barcode]['name'],
                                           price=self.goods_dict[barcode]['price'],
                                           category=self.goods_dict[barcode]['category'])
            session.add(product)
        session.commit()
        session.close()

    def merge_with_main_db(self):
        """This func merge personal db with main goods db."""

        session = Session()
        for x in self.new_goods_barcode:
            new_product = session.query(self.supermarket_orm)\
                                            .filter_by(barcode=x).first()
            exist_product = session.query(Product)\
                                   .filter(Product.barcode == new_product.barcode)\
                                   .scalar()
            if exist_product:
                exec('exist_product.barcode_{} = new_product.barcode'.format(self.supermarket_name))
            else:
                new_product = Product(barcode=new_product.barcode,
                                      name=new_product.name,
                                      category=new_product.category)
                exec('new_product.barcode_{} = new_product.barcode'.format(self.supermarket_name))
                session.add(new_product)
            session.commit()

    def update(self):
        """This func download and parse goods data
        then save him to personal supermarket db
        and merge personal db with main db."""

        start_time = time.time()
        self.goods_dict = self.get_goods_dict()
        end_time = time.time()
        self.metadata['download_time'] = round(end_time-start_time, 2)
        self.metadata['products_count'] = len(self.goods_dict)

        start_time = time.time()
        self.save_to_db()
        end_time = time.time()
        self.metadata['save_to_db_time'] = round(end_time-start_time, 2)
        self.metadata['new_products_count'] = len(self.new_goods_barcode)

        start_time = time.time()
        self.merge_with_main_db()
        end_time = time.time()
        self.metadata['merge_time'] = round(end_time-start_time, 2)

    def get_metadata(self):
        """Return dict with time and goods count values."""
        print(self.metadata)
        return self.metadata


class Auchan(Supermarket):
    def __init__(self):
        self.auchan_categories = {'beer': 'beer', 'vodka': 'vodka',
                                  'wine': 'wine', 'cognac': 'cognac',
                                  'champagne': 'champagne-sparkling-wine'}
        self.auchan_dict = {}
        super().__init__(AuchanProduct, 'auchan')

    def parse_data(self, json_data, category):
        """Parse JSON of category and return dictionary of goods from Auchan."""

        data_dict = {}
        product_list = json.loads(json_data)['responses'][0]['data']['items'][0]['items']
        for product in product_list:
            name = product['name']
            price = product['price'] / 100
            barcode = product['ean'][1:]
            # url = 'https://auchan.zakaz.ua/uk/0{}/'.format(barcode)
            data_dict.update({barcode: {'name': name, 'price': price,
                                        'category': category}})
        return data_dict

    def get_goods_dict(self):
        """Send requests to Auchan API and return dictionary of goods."""

        json_api_url = 'https://auchan.zakaz.ua/api/query.json'
        data = {}
        for category in self.auchan_dict:
            requests_gen = (grequests.post(json_api_url, json=json_data) for json_data in self.auchan_dict[category])
            response_list = grequests.map(requests_gen)
            for json_response in response_list:
                catalog_data = self.parse_data(json_response.text, category)
                data.update(catalog_data)
        return data

    def generate_url(self):
        """This func generate dynamic dict of urls for goods categories."""

        api_url = 'https://auchan.zakaz.ua/api/query.json'
        json_template = JSON_template.copy()
        for category_name in self.auchan_categories:
            json_template['request'][0]['args']['slugs'][0] = self.auchan_categories[category_name]
            json_data = requests.post(api_url, json=json_template).text
            products_count = \
            json.loads(json_data)['responses'][0]['data']['items'][0][
                                  'facets_base']['total']
            pages_count = math.ceil(products_count / 50)
            json_request_list = []
            for page_num in range(1, int(pages_count + 1)):
                json_template['request'][0]['offset'] = page_num
                json_request_list.append(copy.deepcopy(json_template))

            one_category_dict = {category_name: json_request_list}
            self.auchan_dict.update(one_category_dict)


class MegaMarket(Supermarket):
    def __init__(self):
        self.mm_categories = {'beer': '1090', 'vodka': '1050', 'wine': '1040',
                              'champagne': '1110', 'cognac': '1070'}
        self.mm_dict = {}
        super().__init__(MMProduct, 'mm')

    def parse_data(self, html_code, category):
        """Parse HTML of category and return dictionary of goods from MegaMarket."""

        soup = BeautifulSoup(html_code, 'lxml')
        list_products_html_code = soup.find_all('div', class_='product')
        data_dict = {}
        for product in list_products_html_code:
            product_code_and_name = product.find_all('a')[1]
            product_code = product_code_and_name['href'].split('/')[3]
            name = product_code_and_name.text
            price = product.find('div', class_='price').text.replace(
                ' ', '')[1:]  # del white spaces and '/n'
            data_dict.update({product_code: {'name': name, 'price': price,
                                             'category': category}})
        return data_dict

    def get_goods_dict(self):
        """Request categories url and return dictionary of goods from MegaMarket."""

        urls_list = self.mm_dict.values()
        requests_gen = (grequests.get(url) for url in urls_list)
        response_list = grequests.map(requests_gen)
        data = {}
        for x in range(len(response_list)):
            html_code = response_list[x].text
            category = list(self.mm_dict)[x]
            catalog_data = self.parse_data(html_code, category)
            data.update(catalog_data)
        return data

    def generate_url(self):
        """This func generate dynamic dict of urls for goods categories."""

        for x in self.mm_categories:
            url_template = 'https://megamarket.ua/ua/catalogue/category/{0}?show=48000'
            url = url_template.format(self.mm_categories[x])
            self.mm_dict.update({x: url})


class Novus(Supermarket):
    def __init__(self):
        self.novus_categories = {'beer': 'beer', 'vodka': 'vodka',
                                 'wine': 'wine', 'cognac': 'cognac',
                                 'champagne': 'champagne-sparkling-wine'}
        self.novus_dict = {}
        super().__init__(NovusProduct, 'novus')

    def parse_data(self, html_code, category):
        """Parse HTML of category and return dictionary of goods from Novus."""

        soup = BeautifulSoup(html_code, 'lxml')
        list_products_html_code = soup.find_all('div', class_='one-product')
        data_dict = {}
        for product in list_products_html_code:
            name_and_url = product.find('a', class_='one-product-link')
            name = name_and_url['title']
            # url = 'https://novus.zakaz.ua/uk/{}'.format(name_and_url['href'])
            barcode = name_and_url['href'].split('/')[0][1:]
            if barcode[:4] == 'ovus':  # this line del supermarket's beer on tap
                continue
            prc = product.find(class_='one-product-price')
            price_grn = prc.find('span', class_='grivna').text
            price_coin = prc.find('span', class_='kopeiki').text
            full_price = '{}.{}'.format(price_grn, price_coin)
            data_dict.update({barcode: {'name': name, 'price': full_price,
                                        'category': category}})
        return data_dict

    def get_goods_dict(self):
        """Request categories url and return dictionary of goods from Novus."""

        data = {}
        for category_name in self.novus_dict:
            requests_gen = (grequests.get(url) for url in self.novus_dict[category_name])
            response_list = grequests.map(requests_gen)
            for response in response_list:
                catalog_data = self.parse_data(response.text, category_name)
                data.update(catalog_data)
        return data

    def generate_url(self):
        """This func generate dynamic dict of urls for goods categories."""

        url_template = 'https://novus.zakaz.ua/uk/{category}/?&page={page_num}'
        for x in self.novus_categories:
            url_first_page = url_template.format(category=self.novus_categories[x],
                                                 page_num=1)
            html_code = requests.get(url_first_page).text
            soup = BeautifulSoup(html_code, 'lxml')
            number_max_page = soup.find('div',
                                        class_='pagination pagination-centered')
            number_max_page = int(number_max_page.find_all('a')[-2].text)
            urls = []
            for y in range(1, number_max_page + 1):
                page_url = url_template.format(category=self.novus_categories[x],
                                               page_num=y)
                urls.append(page_url)
            self.novus_dict.update({x: urls})
