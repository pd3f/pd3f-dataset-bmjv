from bs4 import BeautifulSoup
import dataset
from dateparser import parse
import get_retries

base_url = "https://www.bmjv.de/"
start_url = "https://www.bmjv.de/SiteGlobals/Forms/Suche/Gesetzgebungsverfahrensuche_Formular.html?resultsPerPage=25"

# set some random user agent
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:74.0) Gecko/20100101 Firefox/74.0",
}


def remove_session_id(url):
    if url is None:
        return None
    if ";" in url:
        url1, url2 = url.split(";")
        if "?" in url:
            url = url1 + url2.split("?")[1]
        else:
            url = url1
    return url


def fetch(url):
    html_content = get_retries.get(
        url, headers=headers, verbose=True, max_backoff=128
    ).text
    soup = BeautifulSoup(html_content, "lxml")
    return soup


def get_details_pages(url):
    soup = fetch(url)

    results = [
        remove_session_id(base_url + x["href"])
        for x in soup.select(".searchresult h3.teaser a")
    ]
    next_url = soup.select("a.forward.button")
    if len(next_url) == 0:
        return []
    return results + get_details_pages(base_url + next_url[0]["href"])


def get_download_links(soup):
    links = []
    for a in soup.select("a.downloadLink"):
        a_date = a.previous_sibling.text.replace("Datum", "")
        a_href = base_url + a["href"]
        a_text = a.text
        headline = a.find_previous("h2", class_="htype-1").text
        links.append([a_date, a_href, a_text, headline])
    return links


def get_other_links(soup):
    links = []
    for a in soup.select("a.themenLink"):
        a_date = a.previous_sibling.text.replace("Datum", "")
        a_href = base_url + a["href"]
        a_text = a.text
        headline = a.find_previous("h2", class_="htype-1").text

        other = fetch(a_href)
        new_a_href = other.find("a", class_="downloadLink")
        if new_a_href is None:
            a_href = None
        else:
            a_href = base_url + new_a_href["href"]

        links.append([a_date, a_href, a_text, headline])
    return links


def process_details_page(url):
    soup = fetch(url)

    category = soup.select("#content .category")[0]
    for x in category.find_all("span"):
        x.extract()
    doc_type, date = category.text.split("|")[:2]  # sometimes more

    title = soup.select("#content h1")[0]
    for x in title.find_all("span"):
        x.extract()
    title = title.text

    description = "\n\n".join([x.text for x in soup.select("#content p")])

    links = get_download_links(soup) + get_other_links(soup)
    return (
        {
            "title": title,
            "description": description,
            "doc_type": doc_type,
            "date": parse(date, languages=["de"]),
            "ministry": "BMJV",
            "url": url,
        },
        [
            {
                "date": parse(l[0], languages=["de"]),
                "url": remove_session_id(l[1]),
                "text": l[2],
                "title": l[3],
            }
            for l in links
        ],
    )


db = dataset.connect("sqlite:///data.db")
t_dos = db["dossiers"]
t_doc = db["documents"]


detail_pages = get_details_pages(start_url)

for p in detail_pages:
    print(p)
    dossier, docs = process_details_page(p)
    d_id = t_dos.insert(dossier)

    for d in docs:
        d["dossier_id"] = d_id

    t_doc.insert_many(docs)

# process_details_page(
#     "https://www.bmjv.de/SharedDocs/Gesetzgebungsverfahren/DE/VO_Universalschlichtungsstellen.html;jsessionid=4B9015857A672B0196705D85E329B85C.1_cid324"
# )
