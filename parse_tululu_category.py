import argparse
import logging
import os
import json

import requests

from itertools import count
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


def download_book(filename, book_id):
    if os.path.exists(filename):
        logger.info(f'Exist book {filename}')
        return filename
    payload = {'id': ''.join(list(filter(lambda x: x.isdigit(), book_id)))}
    url = 'https://tululu.org/txt.php'
    response = requests.get(url, params=payload)
    response.raise_for_status()
    check_for_redirect(response)
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(response.text)
    logger.info(f'Download book {filename}')
    return filename


def end_page_num():
    response = requests.get('https://tululu.org/l55/')
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    return int(soup.select_one('a.npage:last-child').text) + 1


def get_books_urls(start_page, end_page):
    books_urls = []
    for page in range(start_page, end_page):
        page_response = requests.get(
            'https://tululu.org/l55/',
            params={'page': page})
        page_response.raise_for_status()
        soup = BeautifulSoup(page_response.text, 'lxml')
        for book_tag in soup.select('table.d_book'):
            book_id = book_tag.select_one('a')['href']
            books_urls.append(urljoin('https://tululu.org/', book_id))
        logger.info(f'Process page {page}')
    return books_urls


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
    parser = argparse.ArgumentParser(description='Программа скачивания книг')
    parser.add_argument('--start_page', type=int, default=1, help='С какого номера страницы скачивать, по умолчанию - 1')
    parser.add_argument('--end_page', type=int, default=end_page_num(), help='По какой номер страницы скачивать, по умолчанию - последняя')
    parser.add_argument('--dest_folder', default='media', help='Каталог куда размещать, по умолчанию - media')
    parser.add_argument('--skip_img', action='store_true', help='Не скачивать картинки')
    parser.add_argument('--skip_txt', action='store_true', help='Не скачивать книгу')
    parser.add_argument('--json_path', default='.', help='Путь к файлу с описаниями книг')
    args = parser.parse_args()

    books_folder = os.path.join(
        os.path.dirname(__file__),
        args.dest_folder,
        'books'
        )
    os.makedirs(books_folder, exist_ok=True)
    images_folder = os.path.join(
        os.path.dirname(__file__),
        args.dest_folder,
        'images'
        )
    os.makedirs(images_folder, exist_ok=True)
    json_folder = os.path.join(
        os.path.dirname(__file__),
        args.json_path
        )
    os.makedirs(json_folder, exist_ok=True)

    books_urls = get_books_urls(args.start_page, args.end_page)

    books = []
    for url in books_urls:
        try:
            book = parse_book_page(url)
            filename = make_filename(book['title'], books_folder)
            if not args.skip_img:
                book['img_src'] = download_cover(book['img_src'], images_folder)
            if not args.skip_txt:
                book['book_path'] = download_book(filename, urlparse(url).path)
            books.append(book)
        except HTTPError:
            logger.info(f'No book for {url}')

    with open(os.path.join(json_folder, 'books.json'), 'w', encoding='utf-8') as file:
        json.dump(books, file, ensure_ascii=False)


if __name__ == '__main__':
    main()
