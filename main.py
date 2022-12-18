import requests
import os
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError

def download_txt(url, params, filename, folder='books/'):
    """Функция для скачивания текстовых файлов.
    Args:
        url (str): Cсылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """

    '''params = {'id': book_id}
    response = requests.get(url, params=params)'''
    response = requests.get(url, params=params)
    response.raise_for_status()

    try:
        check_for_redirect(response)
    except requests.HTTPError:
        response_url = response.history[0].url
        print(f'book <{filename}> is not download ')
        return None

    clear_book_name = sanitize_filename(filename)
    file_path = os.path.join(folder, f'{clear_book_name}.txt')
    print(f'{clear_book_name}')

    with open(file_path, 'wb') as file:
        file.write(response.content)

    return file_path

def main():
    # url = "https://dvmn.org/filer/canonical/1542890876/16/"
    # filename = 'dvmn.svg'

    # url = "https://tululu.org/txt.php?id=32168"
    # filename = 'Пески Марса.txt'

    url_template = 'https://tululu.org/txt.php?id='
    url_book_page = 'https://tululu.org/b32168/'

    first_id = 1  # 32168
    folder_name = 'books'
    os.makedirs(folder_name, exist_ok=True)

    for book_id in range(first_id, first_id + 10):

        url = f'https://tululu.org/b{book_id}/'

        response = requests.get(url)
        response.raise_for_status()

        try:
            check_for_redirect(response)
        except requests.HTTPError:
            print(f'book book_id={book_id} is not download ')
            continue


        soup = BeautifulSoup(response.text, 'lxml')

        title_tag = soup.find('h1')
        book_name, author = (name_part.strip() for name_part in title_tag.text.split('::'))
        book_file_name = f'{book_id}. {book_name}'

        url = 'https://tululu.org/txt.php' #f'{url_template}{book_id}'
        params = {'id': book_id}
        download_txt(url, params, book_file_name)
        """response = requests.get(url, params=params)
        response.raise_for_status()

        try:
            check_for_redirect(response)
        except requests.HTTPError:
            print(f'book {book_id} is not download ')
            continue

        clear_book_name = sanitize_filename(book_name)
        filename = os.path.join(folder_name, f'{book_id}. {clear_book_name}.txt')
        print(f'{book_id} - {book_name} - {author} - {clear_book_name}')

        with open(filename, 'wb') as file:
            file.write(response.content)"""


def test():
    # Примеры использования
    url = 'https://tululu.org/txt.php?id=1'

    filepath = download_txt(url, 'Алиби')
    print(filepath)  # Выведется books/Алиби.txt

    filepath = download_txt(url, 'Али/би', folder='books/')
    print(filepath)  # Выведется books/Алиби.txt

    filepath = download_txt(url, 'Али\\би', folder='txt/')
    print(filepath)  # Выведется txt/Алиби.txt


if __name__ == '__main__':
    main()
    #test()
