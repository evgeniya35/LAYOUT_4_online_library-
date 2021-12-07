import logging
import os


import requests

from pathvalidate import sanitize_filename
from requests.models import HTTPError
from bs4 import BeautifulSoup

logger = logging.getLogger('logger_main')

def check_for_redirect(response):
    if response.history:
        raise HTTPError


def book_title_author(id):
    url = f'https://tululu.org/b{id}'
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    title, author = (el.strip() for el in soup.find('h1').text.split('::'))
    return title, author


def make_filename(id, title, folder='books'):
    filename = f'{id}. {sanitize_filename(title)}.txt'
    return os.path.join(folder, filename)


def load_book(id):
    url = f'https://tululu.org/txt.php?id={id}'
    response = requests.get(url)
    response.raise_for_status()
    try:
        check_for_redirect(response)
        title, author = book_title_author(id)
        filename = make_filename(id, title)
        with open(filename, 'wb') as file:
            file.write(response.content)
        logger.info(f'Save book {filename}')
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
        load_book(id)


if __name__ == '__main__':
    main()