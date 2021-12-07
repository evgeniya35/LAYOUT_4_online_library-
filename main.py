import logging
import os

import requests

from urllib.parse import urljoin, urlparse

from pathvalidate import sanitize_filename
from requests.models import HTTPError, Response
from bs4 import BeautifulSoup


logger = logging.getLogger('logger_main')


def check_for_redirect(response):
    if response.history:
        raise HTTPError


def parse_book_page(id):
    url = f'https://tululu.org/b{id}'
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    title, author = (el.strip() for el in soup.find('h1').text.split('::'))
    img = urljoin(url, soup.find('div', class_='bookimage').find('img')['src'])
    return title, img


def make_filename(id, title, folder='books'):
    filename = f'{id}. {sanitize_filename(title)}.txt'
    return os.path.join(folder, filename)


def load_cover(url, folder='books'):
    filename = os.path.join(
        folder,
        urlparse(url).path.split('/')[-1]
    )
    response = requests.get(url)
    response.raise_for_status()
    with open(filename, 'wb') as file:
        file.write(response.content)


def load_book(id):
    url = f'https://tululu.org/txt.php?id={id}'
    response = requests.get(url)
    response.raise_for_status()
    try:
        check_for_redirect(response)
        title, img = parse_book_page(id)
        load_cover(img)
        filename = make_filename(id, title)
        with open(filename, 'wb') as file:
            file.write(response.content)
        logger.info(f'Save book {filename} {img}')
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