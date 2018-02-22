import time
import os

from flask import Flask
from parser import MegaMarket, Auchan, Novus
from config import BOT_API_URL, SECRET_URL_FOR_UPDATE
from requests import post

app = Flask(__name__)


@app.route("/")
def index():
    return "All ok!\nHello world"


@app.route(SECRET_URL_FOR_UPDATE)
def data_update():
    first = time.time()

    auchan = Auchan()
    mm = MegaMarket()
    novus = Novus()

    auchan.update()
    send_to_bot(auchan.get_metadata())

    mm.update()
    send_to_bot(mm.get_metadata())

    novus.update()
    send_to_bot(novus.get_metadata())

    second = time.time()
    send_to_bot({'full_time': round(second - first, 3)})
    return "Succsess! was updated"


def send_to_bot(data_dict):
    print(data_dict)
    post(BOT_API_URL, data=data_dict)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
