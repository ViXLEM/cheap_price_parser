import grequests
import requests
import json
import time

from bs4 import BeautifulSoup
from auchan_request_template import JSON_template
from models import Session
from models import Product
from categories_url import novus_dict, mm_dict


class Supermarket():
    def __init__(self, orm, name):
        self.metadata = {'products_count': '', 'new_products_count': '',
                         'download_time': '', 'save_to_db_time': '', 'merge_time': ''}
        start_time = time.time()
        self.goods_dict = self.get_goods_dict()
        end_time = time.time()
        self.metadata['download_time'] = round(end_time-start_time, 2)
        self.metadata['products_count'] = len(self.goods_dict)
        self.supermarket_orm = orm
        self.supermarket_name = name
        self.new_goods_barcode = []

    def save_to_db(self):
        start_time = time.time()
        session = Session()

        for x in session.query(self.supermarket_orm).all():  # deactivate all products
            x.active = False
        session.commit()

        for barcode in self.goods_dict.keys():
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
        end_time = time.time()
        self.metadata['save_to_db_time'] = round(end_time-start_time, 2)
        self.metadata['new_products_count'] = len(self.new_goods_barcode)

    def merge_with_main_db(self):
        start_time = time.time()
        session = Session()
        for x in self.new_goods_barcode:
            new_product = session.query(self.supermarket_orm).filter_by(barcode=x).first()
            exist_product = session.query(Product).filter(Product.barcode == new_product.barcode).scalar()
            if exist_product:
                exec('exist_product.barcode_{} = new_product.barcode'.format(self.supermarket_name))
            else:
                new_product = Product(barcode=new_product.barcode,
                                      name=new_product.name,
                                      category=new_product.category)
                exec('new_product.barcode_{} = new_product.barcode'.format(self.supermarket_name))
                session.add(new_product)
            session.commit()
        end_time = time.time()
        self.metadata['merge_time'] = round(end_time-start_time, 2)

    def get_metadata(self):
        print(self.metadata)


class MegaMarket(Supermarket):

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
            data_dict.update({product_code: {'name': name, 'price': price, 'category': category}})
        return data_dict

    def get_goods_dict(self):
        """Request categories url and return dictionary of goods from MegaMarket."""

        urls_list = mm_dict.values()
        requests_gen = (grequests.get(url) for url in urls_list)
        response_list = grequests.map(requests_gen)
        data = {}
        for x in range(len(response_list)):
            html_code = response_list[x].text
            category = list(mm_dict)[x]
            catalog_data = self.parse_data(html_code, category)
            data.update(catalog_data)
        return data


class Auchan(Supermarket):

    def parse_data(self, json_data):
        """Parse JSON of category and return dictionary of goods from Auchan."""

        data_dict = {}
        product_list = json.loads(json_data)['responses'][0]['data']['items'][0]['items']
        for product in product_list:
            name = product['name']
            price = product['price'] / 100
            barcode = product['ean'][1:]
            url = 'https://auchan.zakaz.ua/uk/0{}/'.format(barcode)
            data_dict.update({barcode: {'name': name, 'price': price}})
        return data_dict

    def get_goods_dict(self):
        """Send requests to Auchan API and return dictionary of goods."""

        json_api_url = 'https://auchan.zakaz.ua/api/query.json'
        data = {}
        for page_number in range(1, 5):
            JSON_template['request'][0]['offset'] = page_number
            json_response = requests.post(json_api_url, json=JSON_template)
            catalog_data = self.parse_data(json_response.text)
            data.update(catalog_data)
        return data


class Novus(Supermarket):
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
            data_dict.update(
                {barcode: {'name': name, 'price': full_price, 'category': category}})
        return data_dict

    def get_goods_dict(self):
        """Request categories url and return dictionary of goods from Novus."""

        data = {}
        for category_name in novus_dict:
            requests_gen = (grequests.get(url) for url in novus_dict[category_name])
            response_list = grequests.map(requests_gen)
            for response in response_list:
                catalog_data = self.parse_data(response.text, category_name)
                data.update(catalog_data)
        return data
