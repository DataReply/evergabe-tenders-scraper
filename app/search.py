from __future__ import annotations

from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class EvergabeSearcher:
    def __init__(self) -> None:
        self.base_url: str = "https://www.evergabe-online.de"
        self.referer_url: str = f"{self.base_url}/search.html?2"
        self.search_form_url: str = (
            f"{self.base_url}/search.html?1-1.0-searchPanel-searchForm-submitButton"
        )
        self.headers = {
            "Accept": "application/xml, text/xml, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": self.base_url,
            "Referer": self.referer_url,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-GPC": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "Wicket-Ajax": "true",
            "Wicket-Ajax-BaseURL": "search.html?2",
            "X-Requested-With": "XMLHttpRequest",
            "sec-ch-ua": '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
        }
        self.session = self._get_session()

    def _get_session(self) -> requests.Session:
        options = Options()
        options.add_argument("--headless=new")
        driver = webdriver.Chrome(options=options)

        # load twice the search link, necessary to load cookies correctly
        [driver.get(self.referer_url) for _ in range(2)]

        cookies = driver.get_cookies()
        driver.quit()

        session = requests.Session()
        for cookie in cookies:
            session.cookies.set(name=cookie["name"], value=cookie["value"])
        return session

    def search(self, search_string: str, period_from: str) -> pd.DataFrame:
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

        response = self.session.post(
            self.search_form_url, headers=self.headers, data=form_data
        )
        return self._parse_response(response=response)

    def _parse_response(self, response: requests.Response) -> pd.DataFrame:
        results = response.text
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
                full_link = urljoin(self.base_url, relative_link)

            row = []
            row.append(title)
            row.append(full_link)
            row.extend([cell.get_text(separator=" ", strip=True) for cell in cells[1:]])

            if len(row) == len(headers):
                data_rows.append(row)

        df = pd.DataFrame(data_rows, columns=headers)
        return df
