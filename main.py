import click
import jsonpickle
from typing import List, Tuple
from queue import Queue
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

PagePath = Tuple[int, ...]


class Page:
    path: PagePath
    title: str
    article: str
    answers: List[str]

    def __init__(self, page_path: PagePath, title: str, article: str, answers: List[str]):
        self.path = page_path
        self.title = title
        self.article = article
        self.answers = answers


class PageDriver:
    driver: WebDriver
    title: str
    article: str
    answer_els: List[WebElement]

    def __init__(self, driver: WebDriver):
        self.driver = driver

        self.title = driver.find_element_by_class_name('at-story__title').text
        self.article = driver.find_element_by_css_selector(
            '.at-story__article article').get_attribute('innerHTML')
        self.answer_els = driver.find_elements_by_css_selector(
            '.at-story__answers ul li a')

    def answers(self):
        return list(map(lambda el: el.text, self.answer_els))

    def click_answer(self, answer_id: int):
        self.answer_els[answer_id].click()
        return PageDriver(self.driver)

    def navigate(self, *page_path: PagePath):
        if page_path:
            (answer_id, *rest) = page_path
            page = self.click_answer(answer_id)
            return page.navigate(*rest)
        else:
            return self

    def restart(self):
        self.driver.find_element_by_css_selector(
            '.at-button--restart:nth-child(2)').click()
        return PageDriver(self.driver)

    def serialize(self, page_path: PagePath):
        return Page(page_path, self.title, self.article, self.answers())


def request_interceptor(request):
    if not request.path.starts_with('https://instory.su/'):
        request.abort()

@click.command()
@click.argument('url')
@click.option('--pages-file', default='data/pages.json')
def download_story(url: str, pages_file: str):
    print("Downloading story at", url, "and saving as", pages_file, flush=True)

    # configure jsonpickle to preserve utf-8 strings instead of \u escape sequences
    jsonpickle.load_backend('simplejson', 'dumps', 'loads', ValueError)
    jsonpickle.set_preferred_backend('simplejson')
    jsonpickle.set_encoder_options('simplejson', ensure_ascii=False)

    # configure Selenium
    chrome_options = Options()
    chrome_options.headless = True
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(1)
    driver.request_interceptor = request_interceptor

    print("Opening", url)
    driver.get(url)
    page_driver = PageDriver(driver)

    print("Opening", pages_file, "for writing")
    with open(pages_file, 'w') as f:
        print("Starting main loop", flush=True)

        queue: "Queue[PagePath]" = Queue()
        queue.put(())

        while not queue.empty():
            page_path = queue.get()

            # open page
            print(page_path, end=' ', flush=True)
            page_driver = page_driver.navigate(*page_path)

            # save page to file
            page = page_driver.serialize(page_path)
            page_json = jsonpickle.encode(page, unpicklable=True, indent=2 * ' ')
            f.write(page_json)
            f.write('\n')

            # add answer pages to queue
            for answer_id in range(len(page_driver.answers())):
                new_page_path = (*page_path, answer_id)
                queue.put(new_page_path)

            # return to root page
            print(page_driver.article[:50], flush=True)
            page_driver = page_driver.restart()

if __name__ == '__main__':
    download_story()
