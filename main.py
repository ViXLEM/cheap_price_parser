import time
import os

from flask import Flask
from parser import MegaMarket, Auchan, Novus

app = Flask(__name__)


@app.route("/")
def index():
    return "hello"


@app.route("/update")
def data_update():
    main()
    return "Succsess! was updated"


def main():
    first = time.time()

    auchan = Auchan()
    auchan.update()
    print(auchan.get_metadata())

    mm = MegaMarket()
    mm.update()
    print(mm.get_metadata())

    novus = Novus()
    novus.update()
    print(novus.get_metadata())

    second = time.time()
    print(round(second-first, 3))


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
