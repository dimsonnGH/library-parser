from bs4 import BeautifulSoup
import requests
import os
from main import get_page, parse_book_page, eprint, make_download_folders, download_book_collection
from main import BASE_URL, TEXTS_FOLDER
from urllib.parse import urljoin
import json
import argparse
import time


def parse_category_page(response_url, html, books_description):
    soup = BeautifulSoup(html, 'lxml')

    img_tags = soup.select('.bookimage a')
    for img_tag in img_tags:
        book_url = img_tag['href']
        book_url = urljoin(response_url, book_url)

        print(book_url)

        response = get_page(book_url)
        book_html = response.text
        book_properties = parse_book_page(book_html, book_url)
        books_description.append(book_properties)


def main():
    parser = argparse.ArgumentParser(description='Download science fiction books from tululu.org')
    parser.add_argument('--start_page', type=int, default=1, help='First science fiction catalog page, default = 1')
    parser.add_argument('--end_page', type=int, help='Last science fiction catalog page, default = 1')
    parser.add_argument('--dest_folder', type=str, default='books', help='Folder to download content')
    parser.add_argument('--skip_imgs', action='store_true', help='Skip download images')
    parser.add_argument('--skip_txt', action='store_true', help='Skip download texts')

    args = parser.parse_args()

    start_url = f'{BASE_URL}/l55/'

    response = get_page(start_url)
    html = response.text
    soup = BeautifulSoup(html, 'lxml')
    tags = soup.select('a.npage')
    max_page = int(tags[-1].text)
    end_page = max(args.end_page, max_page) if args.end_page else max_page

    books_description = []
    delay_value = 60
    delay = 0
    for page_num in range(args.start_page, end_page + 1):
        if delay:
            time.sleep(delay)

        if page_num == 1:
            page_num_url = ''
        else:
            page_num_url = f'{page_num}/'

        url = start_url + page_num_url

        try:
            response = get_page(url)
            html = response.text
        except requests.ConnectionError:
            eprint(f'{url}. Connection error.')
            delay = delay_value
            continue
        except requests.HTTPError:
            eprint(f'page {url}> not exists')
            continue

        delay = 0

        parse_category_page(url, html, books_description)

    make_download_folders(args.dest_folder)

    if books_description:
        file_path = os.path.join(args.dest_folder, TEXTS_FOLDER, 'books_description.json')
        with open(file_path, 'wt', encoding="utf-8") as file:
            dumps = json.dumps(books_description, indent=4, ensure_ascii=False)
            file.write(dumps)

    book_collection = (book['url'] for book in books_description)
    download_book_collection(book_collection, args.dest_folder, skip_imgs=args.skip_imgs, skip_txt=args.skip_txt)


if __name__ == '__main__':
    main()
