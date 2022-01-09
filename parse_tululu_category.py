import logging
import os
import json

import requests

from pprint import pp, pprint
from urllib.parse import urljoin, urlparse
from pathvalidate import sanitize_filename
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup


logger = logging.getLogger('logger_main')

def make_filename(title, folder='books'):
    filename = f'{sanitize_filename(title)}.txt'
    return os.path.join(folder, filename)


def check_for_redirect(response):
    if response.history:
        raise HTTPError


def download_cover(cover_url, folder='images'):
    filename = os.path.join(
        folder,
        urlparse(cover_url).path.split('/')[-1]
    )
    if os.path.exists(filename):
        logger.info(f'Exist cover {filename}')    
        return filename
    response = requests.get(cover_url)
    response.raise_for_status()
    with open(filename, 'wb') as file:
        file.write(response.content)
    logger.info(f'Download cover {filename}')
    return filename


def download_book(filename, id):
    if os.path.exists(filename):
        logger.info(f'Exist book {filename}')    
        return filename
    payload = {'id': int(''.join(list(filter(lambda x: x.isdigit(), id))))}
    url = 'https://tululu.org/txt.php'
    response = requests.get(url, params=payload)
    response.raise_for_status()
    check_for_redirect(response)
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(response.text)
    logger.info(f'Download book {filename}')
    return filename


def fetch_pages(url):
    response = requests.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'lxml')


def parse_book_page(url):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    soup = BeautifulSoup(response.text, 'lxml')
    title, author = (el.strip() for el in soup.select_one('h1').text.split('::'))
    cover_url = urljoin(url, soup.select_one('div.bookimage img')['src'])
    comments = [comment.text.split(')')[1] for comment in soup.select('div.texts')]
    genres = [genre.text for genre in soup.select('span.d_book a')]
    links = [lnk.text for lnk in soup.select('table.d_book a')]
    # ToDo print(links) парсить ссылку на txt
    book = {
        'title': title,
        'author': author,
        'img_src': cover_url,
        'genres': genres,
        'comments': comments
    }
    logger.info(f'Parse book page {url}')
    return book


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    books_folder = os.path.join(
        os.path.dirname(__file__),
        'books'
        )
    os.makedirs(books_folder, exist_ok=True)
    images_folder = os.path.join(
        os.path.dirname(__file__),
        'images'
        )
    os.makedirs(images_folder, exist_ok=True)
    site = 'http://tululu.org/l55/'
    max_pages = 2
    books = []
    for page_num in range(1, max_pages):
        page = fetch_pages(f'{site}/{page_num}/')
        for book_tag in page.select('table.d_book'):
            book_id = book_tag.select_one('a')['href']
            book_url = urljoin(site, book_id)
            try:
                book = parse_book_page(book_url)
                filename = make_filename(book['title'], books_folder)
                book['img_src'] = download_cover(book['img_src'], images_folder)
                book['book_path'] = download_book(filename, book_id)
                books.append(book)
            except HTTPError:
                logger.info(f'No book for {book_url}')
    if books:
        with open(os.path.join(os.path.dirname(__file__), 'books.json'), 'w', encoding='utf-8') as file:
            json.dump(books, file, ensure_ascii=False)
        

if __name__ == '__main__':
    main()