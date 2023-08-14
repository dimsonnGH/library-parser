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

BASE_URL = 'https://tululu.org'
TEXTS_FOLDER = 'texts'
IMGS_FOLDER = 'imgs'


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def make_download_folders(dest_folder):
    for folder_name in [TEXTS_FOLDER, IMGS_FOLDER, ]:
        os.makedirs(os.path.join(dest_folder, folder_name), exist_ok=True)


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def download_txt(url, params, filename, folder):
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

    with open(file_path, 'w', encoding="utf-8") as file:
        file.write(response.text)

    return file_path


def download_image(url, filename, folder):
    """Функция для скачивания изображений.
    Args:
        url (str): Адрес ресурса, с которого нужно скачать изображение.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранёно изображение.
    """

    response = requests.get(url)
    response.raise_for_status()

    file_path = os.path.join(folder, f'{filename}')

    with open(file_path, 'wb') as file:
        file.write(response.content)

    return file_path


def get_page(url):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)

    return response


def parse_book_page(html, url):
    soup = BeautifulSoup(html, 'lxml')

    title_tag = soup.select_one('h1')
    name, author = (name_part.strip() for name_part in title_tag.text.split('::'))

    img_url = soup.select_one('.bookimage img')['src']
    url_parts = urlparse(img_url)
    img_path = url_parts.path

    book_properties = {
        'name': name,
        'author': author,
        'url': url,
        'img_url': img_url,
        'img_name': unquote(os.path.split(img_path)[-1]),
        'comments': [tag.text for tag in soup.select('.texts .black')],
        'genres': [tag.text for tag in soup.select('span.d_book a')],
    }

    return book_properties


def download_book_collection(book_collection, base_folder, **kwargs):
    delay_value = 60

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
            delay = delay_value
            continue
        except requests.HTTPError:
            eprint(f'page {url}> not exists')
            continue

        delay = 0

        book_properties = parse_book_page(book_html, url)
        book_file_name = f"{book_id}. {book_properties['name']}"
        url = f'{BASE_URL}/txt.php'
        params = {'id': book_id}

        if 'skip_txt' not in kwargs or not kwargs['skip_txt']:
            try:
                download_txt(url, params, book_file_name, os.path.join(base_folder, TEXTS_FOLDER))
            except requests.ConnectionError:
                eprint(f'{url}. Connection error.')
                delay = delay_value
                continue
            except requests.HTTPError:
                eprint(f'book id = {book_id} <{book_properties["name"]}> is not downloaded')
                continue

        if 'skip_imgs' not in kwargs or not kwargs['skip_imgs']:
            img_url = urljoin(response_url, book_properties['img_url'])
            try:
                download_image(img_url, book_properties['img_name'], os.path.join(base_folder, IMGS_FOLDER))
            except requests.ConnectionError:
                eprint(f'{url}. Connection error.')
                delay = delay_value
                continue
            except requests.HTTPError:
                eprint(f'image {img_url} is not downloaded')
                continue


def main():
    parser = argparse.ArgumentParser(description='Download books from tululu.org')
    parser.add_argument('--start_id', type=int, default=1, help='First book id, default = 1')
    parser.add_argument('--end_id', type=int, default=1, help='Last book id, default = 1')
    parser.add_argument('--dest_folder', type=str, default='books', help='Folder to download content')
    parser.add_argument('--skip_imgs', action='store_true', help='Skip download images')
    parser.add_argument('--skip_txt', action='store_true', help='Skip download texts')
    args = parser.parse_args()

    if args.start_id > args.end_id:
        print('start_id cannot be greater than the end_id')
        return

    book_collection = (book_id for book_id in range(args.start_id, args.end_id + 1))

    make_download_folders(args.dest_folder)

    download_book_collection(book_collection, args.dest_folder, skip_imgs=args.skip_imgs, skip_txt=args.skip_txt)


if __name__ == '__main__':
    main()
