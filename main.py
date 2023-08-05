import time
from builtins import isinstance

import requests
import os
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlparse, unquote
import argparse
import sys
import re


DELAY_VALUE = 60
BASE_URL = 'https://tululu.org'

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def make_download_folders():
    for folder_name in ['books', 'imgs', ]:
        os.makedirs(folder_name, exist_ok=True)

def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def download_txt(url, params, filename, folder='books/'):
    """Функция для скачивания текстовых файлов.
    Args:
        url (str): Адрес ресурса, с которого нужно скачать текст.
        params (dict): Параметры запроса
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """

    response = requests.get(url, params=params)
    response.raise_for_status()
    check_for_redirect(response)

    clear_book_name = sanitize_filename(filename)
    file_path = os.path.join(folder, f'{clear_book_name}.txt')

    with open(file_path, 'wb') as file:
        file.write(response.content)

    return file_path


def download_image(url, filename, folder='imgs/'):
    """Функция для скачивания изображений.
    Args:
        url (str): Адрес ресурса, с которого нужно скачать изображение.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """

    response = requests.get(url)
    response.raise_for_status()

    file_path = os.path.join(folder, f'{filename}')

    with open(file_path, 'w', encoding="utf-8") as file:
        file.write(response.text)

    return file_path

def get_page(url):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)

    return response

def parse_book_page(html, url):


    soup = BeautifulSoup(html, 'lxml')

    title_tag = soup.find('h1')
    name, author = (name_part.strip() for name_part in title_tag.text.split('::'))

    img_url = soup.find('div', class_='bookimage').find('img')['src']
    url_parts = urlparse(img_url)
    img_path = url_parts.path

    book_properties = {
        'name': name,
        'author': author,
        'url': url,
        'img_url': img_url,
        'img_name': unquote(os.path.split(img_path)[-1]),
        'comments': [tag.find('span', class_='black').text for tag in soup.findAll('div', class_='texts')],
        'genres': [tag.text for tag in soup.find('span', class_='d_book').findAll('a')],
    }

    return book_properties

def download_book_collection(book_collection):

    delay = 0
    for book_descriptor in book_collection:

        if isinstance(book_descriptor, int):
            book_id = book_descriptor
            url = f'{BASE_URL}/b{book_id}/'
        elif isinstance(book_descriptor, str):
            url = book_descriptor
            m = re.search(f'{BASE_URL}/b(.+)/', url)
            if m:
                book_id = m.group(1)
            else:
                eprint(f'{url}. Incorrect url format. Book id missing')
                continue
        else:
            eprint(f'{book_descriptor}. Incorrect book descriptor')
            continue

        if delay:
            time.sleep(delay)

        try:
            response = get_page(url)
            book_html = response.text
            response_url = response.url
        except requests.ConnectionError:
            eprint(f'{url}. Connection error.')
            delay = DELAY_VALUE
            continue
        except requests.HTTPError:
            eprint(f'page {url}> not exists')
            continue

        delay = 0

        book_properties = parse_book_page(book_html, url)
        book_file_name = f"{book_id}. {book_properties['name']}"
        url = f'{BASE_URL}/txt.php'
        params = {'id': book_id}

        try:
            download_txt(url, params, book_file_name)
        except requests.ConnectionError:
            eprint(f'{url}. Connection error.')
            delay = DELAY_VALUE
            continue
        except requests.HTTPError:
            eprint(f'book id = {book_id} <{book_properties["name"]}> is not downloaded')
            continue

        img_url = urljoin(response_url, book_properties['img_url'])

        try:
            download_image(img_url, book_properties['img_name'])
        except requests.ConnectionError:
            eprint(f'{url}. Connection error.')
            delay = DELAY_VALUE
            continue
        except requests.HTTPError:
            eprint(f'image {img_url} is not downloaded')
            continue


def main():
    parser = argparse.ArgumentParser(description='Download books from tululu.org')
    parser.add_argument('--start_id', type=int, default=1, help='First book id, default = 1')
    parser.add_argument('--end_id', type=int, default=1, help='Last book id, default = 1')
    args = parser.parse_args()

    if args.start_id > args.end_id:
        print('start_id cannot be greater than the end_id')
        return

    book_collection = (book_id for book_id in range(args.start_id, args.end_id + 1))

    download_book_collection(book_collection)

if __name__ == '__main__':
    main()
