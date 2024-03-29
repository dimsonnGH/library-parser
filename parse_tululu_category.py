from bs4 import BeautifulSoup
import requests
import os
from main import get_page, parse_book_page, eprint, make_download_folders, download_book_collection
from main import BASE_URL, TEXTS_FOLDER
from urllib.parse import urljoin
import json
import argparse
import time


def parse_category_page(response_url, html, book_descriptions):
    soup = BeautifulSoup(html, 'lxml')

    new_book_descriptions = [*book_descriptions]
    img_tags = soup.select('.bookimage a')
    for img_tag in img_tags:
        book_url = img_tag['href']
        book_url = urljoin(response_url, book_url)

        try:
            response = get_page(book_url)
            book_html = response.text
            book_properties = parse_book_page(book_html, book_url)
            new_book_descriptions.append(book_properties)
        except requests.ConnectionError:
            eprint(f'{book_url}. Connection error.')
            time.sleep(20)
            continue
        except requests.HTTPError:
            eprint(f'page {book_url}> not exists')
            continue

    return new_book_descriptions


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

    book_descriptions = []
    delay_value = 60
    for page_num in range(args.start_page, end_page + 1):

        url = urljoin(start_url, str(page_num))

        try:
            response = get_page(url)
            book_descriptions = parse_category_page(url, response.text, book_descriptions)
        except requests.ConnectionError:
            eprint(f'{url}. Connection error.')
            time.sleep(delay_value)
            continue
        except requests.HTTPError:
            eprint(f'page {url}> not exists')
            continue

    make_download_folders(args.dest_folder)

    if book_descriptions:
        file_path = os.path.join(args.dest_folder, TEXTS_FOLDER, 'book_descriptions.json')
        with open(file_path, 'wt', encoding="utf-8") as file:
            json.dump(book_descriptions, file, indent=4, ensure_ascii=False)

    book_collection = (book['url'] for book in book_descriptions)
    download_book_collection(book_collection, args.dest_folder, skip_imgs=args.skip_imgs, skip_txt=args.skip_txt)


if __name__ == '__main__':
    main()
