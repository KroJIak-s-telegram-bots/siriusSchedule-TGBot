import requests
from bs4 import BeautifulSoup

from utils.const import ConstPlenty

const = ConstPlenty()

def getUrlImgWithCat():
    response = requests.get(const.cats.url)
    bs = BeautifulSoup(response.text, 'lxml')
    imgObject = bs.find('img', 'hot-random-image')
    url = imgObject['src'] if imgObject['src'][0] != '<' else imgObject['href']
    return url

if __name__ == '__main__':
    print(getUrlImgWithCat())