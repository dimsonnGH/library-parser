import requests
import os


def main():
    #url = "https://dvmn.org/filer/canonical/1542890876/16/"
    #filename = 'dvmn.svg'

    #url = "https://tululu.org/txt.php?id=32168"
    #filename = 'Пески Марса.txt'

    url_template = "https://tululu.org/txt.php?id="

    first_id = 32168
    folder_name = 'books'
    os.makedirs(folder_name, exist_ok=True)

    for book_id in range(first_id, first_id + 10):

        url = f'{url_template}{book_id}'
        response = requests.get(url)
        response.raise_for_status()
        filename = os.path.join(folder_name, f'book_{book_id}.txt')

        with open(filename, 'wb') as file:
            file.write(response.content)


if __name__ == '__main__':
    main()
