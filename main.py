import logging
import os

import requests
from requests.models import HTTPError
from bs4 import BeautifulSoup

logger = logging.getLogger('logger_main')

def check_for_redirect(response):
    if response.history:
        raise HTTPError

def get_book(id):
    url = f'https://tululu.org/b{id}'
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    title, author = (el.strip() for el in soup.find('h1').text.split('::'))
    print(title, author)

def main1():
    get_book(1)

def load_book(id, filename):
    url = f'https://tululu.org/txt.php?id={id}'
    response = requests.get(url)
    response.raise_for_status()
    try:
        check_for_redirect(response)
        with open(filename, 'wb') as file:
            file.write(response.content)
        logger.info(f'Download book {id}')
    except HTTPError:
        pass


def main():
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger.setLevel(logging.INFO)    
    folder = os.path.join(
        os.path.dirname(__file__),
        'books'
        )
    os.makedirs(folder, exist_ok=True)
    for id in range(1, 11):
        filename = os.path.join(folder, f'id{id}.txt')
        if not os.path.isfile(filename):
            load_book(id, filename)


if __name__ == '__main__':
    main1()