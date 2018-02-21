import time

from parser import MegaMarket, Auchan, Novus


def main():
    first = time.time()

    auchan = Auchan()
    auchan.update()
    auchan.get_metadata()

    mm = MegaMarket()
    mm.update()
    mm.get_metadata()

    novus = Novus()
    novus.update()
    novus.get_metadata()

    second = time.time()
    print(round(second-first, 3))


if __name__ == '__main__':
    main()
