import time

from parser import MegaMarket, Auchan, Novus
from models import AuchanProduct, NovusProduct, MMProduct


def main():
    first = time.time()

    mm = MegaMarket(MMProduct, 'mm')
    mm.save_to_db()
    mm.merge_with_main_db()
    mm.get_metadata()

    auchan = Auchan(AuchanProduct, 'auchan')
    auchan.save_to_db()
    auchan.merge_with_main_db()
    auchan.get_metadata()

    novus = Novus(NovusProduct, 'novus')
    novus.save_to_db()
    novus.merge_with_main_db()
    novus.get_metadata()

    second = time.time()
    print(round(second-first, 3))


if __name__ == '__main__':
    main()
