import time

import requests
import os
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlparse, unquote
import argparse
import sys


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

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

    with open(file_path, 'wb') as file:
        file.write(response.content)

    return file_path

def get_book_page(url):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)

    return response

def parse_book_page(html):

    soup = BeautifulSoup(html, 'lxml')

    title_tag = soup.find('h1')
    name, author = (name_part.strip() for name_part in title_tag.text.split('::'))

    img_url = soup.find('div', class_='bookimage').find('img')['src']
    url_parts = urlparse(img_url)
    img_path = url_parts.path

    book_properties = {
        'name': name,
        'author': author,
        'img_url': img_url,
        'img_name': unquote(os.path.split(img_path)[-1]),
        'comments': [tag.find('span', class_='black').text for tag in soup.findAll('div', class_='texts')],
        'genres': [tag.text for tag in soup.find('span', class_='d_book').findAll('a')],
    }

    return book_properties


def main():
    parser = argparse.ArgumentParser(description='Download books from tululu.org')
    parser.add_argument('--start_id', type=int, default=1, help='First book id, default = 1')
    parser.add_argument('--end_id', type=int, default=1, help='Last book id, default = 1')
    args = parser.parse_args()

    if args.start_id > args.end_id:
        print('start_id cannot be greater than the end_id')
        return

    DELAY_VALUE = 60

    for folder_name in ['books', 'imgs', ]:
        os.makedirs(folder_name, exist_ok=True)

    base_url = 'https://tululu.org'
    delay = 0
    for book_id in range(args.start_id, args.end_id + 1):

        if delay:
            time.sleep(delay)

        url = f'{base_url}/b{book_id}/'

        try:
            response = get_book_page(url)
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

        book_properties = parse_book_page(book_html)
        book_file_name = f"{book_id}. {book_properties['name']}"
        url = f'{base_url}/txt.php'
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


if __name__ == '__main__':
    main()
