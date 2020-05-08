from pathlib import Path
from urllib.parse import urljoin

import dataset
import get_retries
from bs4 import BeautifulSoup
from joblib import Parallel, delayed
from tqdm import tqdm


db = dataset.connect("sqlite:///data.db")
t_dos = db["dossiers"]
t_doc = db["documents"]

urls = []
for x in t_doc.all():
    if not x["url"] is None:
        urls.append(x["url"])

# set some random user agent
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:74.0) Gecko/20100101 Firefox/74.0",
}


def fetch(url):
    # set some random user agent
    html_content = get_retries.get(
        url, headers=headers, verbose=True, max_backoff=128
    ).text
    soup = BeautifulSoup(html_content, "lxml")
    return soup


def dl(url, fn):
    response = get_retries.get(url, headers=headers, verbose=True, max_backoff=128)

    # sometimes there is an additional HTML page
    if "text/html" in response.headers["content-type"]:
        print(url)
        soup = BeautifulSoup(response.text, "lxml")
        link = soup.find("a", class_="Publication")
        if link is None:
            link = soup.find("a", class_="downloadLink")

        url = urljoin(base_url, link["href"])
        dl(url, fn)

    assert "application/pdf" in response.headers["content-type"], (
        url + response.headers["content-type"]
    )
    with open("pdfs/" + fn, "wb") as f:
        try:
            f.write(response.content)
        except Exception as e:
            print(e, url, response)


base_url = "https://www.bmjv.de"


def do_url(url):
    fn = url.split(";")[0]
    fn = fn.split("/")[-1]
    fn = fn.split("__blob=publicationFile")[0]
    if not fn.endswith(".pdf"):
        fn += ".pdf"
    if Path("pdfs/" + fn).exists():
        return

    link = fetch(url).find("a", class_="downloadLink")
    if link is None:
        print(url)
        link = url
    else:
        link = urljoin(base_url, link["href"])
    dl(link, fn)


Parallel(n_jobs=10)(delayed(do_url)(u) for u in tqdm(urls))
