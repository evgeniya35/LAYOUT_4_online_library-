import logging
import os

import requests

from urllib.parse import urljoin, urlparse

from pathvalidate import sanitize_filename
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup


logger = logging.getLogger('logger_main')


def check_for_redirect(response):
    if response.history:
        raise HTTPError


def parse_book_page(book_id):
    url = f'https://tululu.org/b{book_id}/'
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    soup = BeautifulSoup(response.text, 'lxml')
    title, author = (el.strip() for el in soup.find('h1').text.split('::'))
    cover_url = urljoin(url, soup.find('div', class_='bookimage').find('img')['src'])
    comments = [comment.text.split(')')[1] for comment in soup.find_all('div', class_='texts')]
    logger.info(f'Parse book page {book_id}')
    return title, cover_url, comments


def make_filename(id, title, folder='books'):
    filename = f'{id}. {sanitize_filename(title)}.txt'
    return os.path.join(folder, filename)


def download_cover(cover_url, folder='books'):
    filename = os.path.join(
        folder,
        urlparse(cover_url).path.split('/')[-1]
    )
    if not os.path.isfile(filename):
        response = requests.get(cover_url)
        response.raise_for_status()
        logger.info(f'Download cover {filename}')
        with open(filename, 'wb') as file:
            file.write(response.content)


def download_book(folder, filename, id):
    url = f'https://tululu.org/txt.php?id={id}'
    response = requests.get(url)
    response.raise_for_status()
    with open(filename, 'wb') as file:
        file.write(response.content)
    logger.info(f'Download book {filename}')


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )    
    folder = os.path.join(
        os.path.dirname(__file__),
        'books'
        )
    os.makedirs(folder, exist_ok=True)
    for book_id in range(1, 11):
        try:
            title, cover_url, comments = parse_book_page(book_id)
            print(title, '\n'.join(comments))
            # filename = make_filename(book_id, title, folder)
            # download_cover(cover_url, folder)
            # download_book(folder, filename, book_id)

        except HTTPError:
            logger.info(f'No book for {book_id}')

if __name__ == '__main__':
    main()