from bs4 import BeautifulSoup
import requests
import os
from main import get_page, parse_book_page, eprint, make_download_folders, download_book_collection
from urllib.parse import urlparse, urljoin
import json


def parse_category_page(response_url, html, books_description):
    soup = BeautifulSoup(html, 'lxml')

    img_tags = soup.findAll('div', class_='bookimage')
    for img_tag in img_tags:
        book_url = img_tag.find('a')['href']
        book_url = urljoin(response_url, book_url)

        response = get_page(book_url)
        book_html = response.text
        book_properties = parse_book_page(book_html, book_url)
        books_description.append(book_properties)


def main():
    start_url = 'https://tululu.org/l55/'

    response = get_page(start_url)
    html = response.text
    soup = BeautifulSoup(html, 'lxml')
    tags = soup.findAll('a', class_='npage')
    page_count = int(tags[-1].text)

    print(f'page_count = {page_count}')

    books_description = []

    for page_num in range(1, page_count + 1):

        if page_num == 1:
            page_num_url = ''
        else:
            page_num_url = f'{page_num}/'

        url = start_url + page_num_url

        try:
            response = get_page(url)
            html = response.text
            # response_url = response.url
        except requests.ConnectionError:
            eprint(f'{url}. Connection error.')
            # delay = DELAY_VALUE
            # continue
        except requests.HTTPError:
            eprint(f'page {url}> not exists')
            # continue

        # delay = 0

        parse_category_page(url, html, books_description)

        #TODO убрать потом
        if len(books_description) >= 100:
            break


    make_download_folders()

    folder = 'books/'
    if books_description:
        file_path = os.path.join(folder, 'books_description.json')
        with open(file_path, 'wt', encoding="utf-8") as file:
            dumps = json.dumps(books_description, indent=4, ensure_ascii=False)
            file.write(dumps)

    book_collection = (book['url'] for book in books_description)
    download_book_collection(book_collection)

if __name__ == '__main__':
    main()
