import argparse
import logging
import os

import requests

from urllib import parse
from urllib.parse import urljoin, urlparse
from pathvalidate import sanitize_filename
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup


logger = logging.getLogger('logger_main')


def check_for_redirect(response):
    if response.history:
        raise HTTPError


def make_filename(id, title, folder='books'):
    filename = f'{id}. {sanitize_filename(title)}.txt'
    return os.path.join(folder, filename)


def download_cover(cover_url, folder='books'):
    filename = os.path.join(
        folder,
        urlparse(cover_url).path.split('/')[-1]
    )
    if not os.path.exists(filename):
        response = requests.get(cover_url)
        response.raise_for_status()
        logger.info(f'Download cover {filename}')
        with open(filename, 'wb') as file:
            file.write(response.content)


def download_book(filename, id):
    payload = {'id': id}
    url = 'https://tululu.org/txt.php'
    response = requests.get(url, params=payload)
    response.raise_for_status()
    check_for_redirect(response)
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(response.text)
    logger.info(f'Download book {filename}')


def parse_book_page(book_id):
    url = f'https://tululu.org/b{book_id}/'
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    soup = BeautifulSoup(response.text, 'lxml')
    title, author = (el.strip() for el in soup.find('h1').text.split('::'))
    cover_url = urljoin(url, soup.find('div', class_='bookimage').find('img')['src'])
    comments = [comment.text.split(')')[1] for comment in soup.find_all('div', class_='texts')]
    genres = [genre.text for genre in soup.find('span', class_='d_book').find_all('a')]
    links = [lnk.text for lnk in soup.find('table', class_='d_book').find_all('a')]
    # ToDo print(links) парсить ссылку на txt
    book = {
        'Заголовок': title,
        'Автор': author,
        'Обложка': cover_url,
        'Жанр': genres,
        'Комментарии': comments
    }
    logger.info(f'Parse book page {book_id}')
    return book


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    parser = argparse.ArgumentParser(description='Программа загрузки книг')
    parser.add_argument('--start_id', type=int, default=1, help='С какого номера книги загружать, по умолчанию 1')
    parser.add_argument('--end_id', type=int, default=9, help='По какой номер книги загружать, по умолчанию 9')
    args = parser.parse_args()
    folder = os.path.join(
        os.path.dirname(__file__),
        'books'
        )
    os.makedirs(folder, exist_ok=True)
    for book_id in range(args.start_id, args.end_id):
        try:
            book = parse_book_page(book_id)
            filename = make_filename(book_id, book['Заголовок'], folder)
            download_cover(book['Обложка'], folder)
            download_book(filename, book_id)
        except HTTPError:
            logger.info(f'No book for {book_id}')

if __name__ == '__main__':
    main()
