import requests
import os
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlparse, unquote
import argparse


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

    try:
        check_for_redirect(response)
    except requests.HTTPError:
        print(f'book <{filename}> is not download ')
        return None

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


def parse_book_page(url):
    response = requests.get(url)
    response.raise_for_status()

    try:
        check_for_redirect(response)
    except requests.HTTPError:
        print(f'book {url} is not download ')
        return

    result = {}

    soup = BeautifulSoup(response.text, 'lxml')

    title_tag = soup.find('h1')
    name, author = (name_part.strip() for name_part in title_tag.text.split('::'))
    result['name'] = name
    result['author'] = author

    img_url = urljoin(response.url, soup.find('div', class_='bookimage').find('img')['src'])
    result['img_url'] = img_url

    url_parts = urlparse(img_url)
    img_path = url_parts.path
    result['img_name'] = unquote(os.path.split(img_path)[-1])

    result['comments'] = [tag.find('span', class_='black').text for tag in soup.findAll('div', class_='texts')]

    result['genres'] = [tag.text for tag in soup.find('span', class_='d_book').findAll('a')]

    return result


def main():
    parser = argparse.ArgumentParser(description='Download books from tululu.org')
    parser.add_argument('--start_id', type=int, default=1, help='First book id, default = 1')
    parser.add_argument('--end_id', type=int, default=1, help='Last book id, default = 1')
    args = parser.parse_args()

    if args.start_id > args.end_id:
        print('start_id cannot be greater than the end_id')
        return

    for folder_name in ['books', 'imgs', ]:
        os.makedirs(folder_name, exist_ok=True)

    for book_id in range(args.start_id, args.end_id):

        url = f'https://tululu.org/b{book_id}/'

        book_properties = parse_book_page(url)

        if not book_properties:
            continue

        book_file_name = f"{book_id}. {book_properties['name']}"

        url = 'https://tululu.org/txt.php'
        params = {'id': book_id}
        download_txt(url, params, book_file_name)

        download_image(book_properties['img_url'], book_properties['img_name'])


if __name__ == '__main__':
    main()
