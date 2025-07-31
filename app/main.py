import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from typing import List, Dict
from bs4 import BeautifulSoup
import pandas as pd
import warnings
from bs4.builder import XMLParsedAsHTMLWarning
from utils import get_date_one_month_from_now
from urllib.parse import urljoin

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

base_url = "https://www.evergabe-online.de"
referer_url = f"{base_url}/search.html?2"
search_form_url = f"{base_url}/search.html?1-1.0-searchPanel-searchForm-submitButton"


def get_cookies() -> List[Dict]:
    options = Options()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)

    # load twice the search link, necessary to load cookies correctly
    [driver.get(referer_url) for _ in range(2)]

    cookies = driver.get_cookies()
    driver.quit()
    return cookies


def perform_search(session: requests.Session) -> requests.Response:
    headers = {
        "Accept": "application/xml, text/xml, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": base_url,
        "Referer": referer_url,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Sec-GPC": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Wicket-Ajax": "true",
        "Wicket-Ajax-BaseURL": "search.html?2",
        "Wicket-FocusedElementId": "id119",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
    }

    form_data = (
        f"simpleSearchParametersPanel%3AkeywordStringGroup%3AsearchString={search_string}&"
        "simpleSearchParametersPanel%3ApublishDateRangeGroup%3ApublishDateRange=ALL&"
        "advancedSearchParameters%3AadvancedSearchParameterPanel%3AplaceStringGroup%3AplaceString=&"
        "advancedSearchParameters%3AadvancedSearchParameterPanel%3AcpvCodeStringGroup%3AcpvCodes%3AcpvCodeViewContainer%3AcpvCodeInputField=&"
        "advancedSearchParameters%3AadvancedSearchParameterPanel%3AdeadlineGroup%3AdeadlineFrom=&"
        "advancedSearchParameters%3AadvancedSearchParameterPanel%3AdeadlineGroup%3AdeadlineTo=&"
        f"advancedSearchParameters%3AadvancedSearchParameterPanel%3AtenderFloatingPeriodGroup%3AtenderFloatingPeriodFrom={period_from}&"
        "advancedSearchParameters%3AadvancedSearchParameterPanel%3AtenderFloatingPeriodGroup%3AtenderFloatingPeriodTo=&"
        "advancedSearchParameters%3AadvancedSearchParameterPanel%3ApublishDateGroup%3ApublishDateFrom=&"
        "advancedSearchParameters%3AadvancedSearchParameterPanel%3ApublishDateGroup%3ApublishDateTo=&"
        "advancedSearchParameters%3AadvancedSearchParameterPanel%3AauthoritiesGroup%3Aauthorities%3Acontrol%3AuserInputTextField=&"
        "searchLinkModal%3Ainput=link&"
        "submitButton=1"
    )

    response = session.post(search_form_url, headers=headers, data=form_data)
    return response


def parse_results(results: str) -> pd.DataFrame:
    soup = BeautifulSoup(results, "lxml")

    table = soup.find("table", id="datatable")
    thead = table.find("thead")
    tbody = table.find("tbody")

    header_row = thead.find("tr", class_="headers")
    headers = [th.get_text(strip=True) for th in header_row.find_all("th")]
    
    headers.insert(1, "Link")

    data_rows = []
    for tr in tbody.find_all("tr"):
        cells = tr.find_all("td")
        if not cells or len(cells) < 1:
            continue

        a_tag = cells[0].find("a")
        title = ""
        full_link = ""
        if a_tag:
            title = a_tag.get_text(strip=True)
            relative_link = a_tag.get("href", "")
            full_link = urljoin(base_url, relative_link)

        row = []
        row.append(title)
        row.append(full_link)
        row.extend([cell.get_text(separator=" ", strip=True) for cell in cells[1:]])

        if len(row) == len(headers):
            data_rows.append(row)

    df = pd.DataFrame(data_rows, columns=headers)
    return df


def main():
    cookies = get_cookies()

    session = requests.Session()
    for cookie in cookies:
        session.cookies.set(name=cookie["name"], value=cookie["value"])

    response = perform_search(session)
    df: pd.DataFrame = parse_results(response.text)
    
    df.to_html("res/final_response.html")
    print("Saved response to 'final_response.html'")

    with open("res/final_response.xml", "w") as f:
        f.write(response.text)
    print("Saved response to 'final_response.xml'")


if __name__ == "__main__":
    search_string = input("search string: ")
    period_from = get_date_one_month_from_now()
    main()
