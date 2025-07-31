import re
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

    def _get_first_page(
        self, search_string: str, period_from: str
    ) -> requests.Response:
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
        return response

    def _get_page(self, url: str):
        response = self.session.get(url=url, headers=self.headers)
        return response

    def _get_other_pages(self, response: requests.Response) -> pd.DataFrame:
        soup = BeautifulSoup(response.text, "lxml")
        spans = soup.select("thead span.goto")

        results = []
        i = 0
        while i < len(spans) - 1:
            # go to the next page
            next_page_relative_url = spans[i + 1].select_one("a").get("href")
            next_page_relative_url = re.sub(
                r"(\d+-\d\.)", r"\g<1>0", next_page_relative_url
            )
            next_page_url = urljoin(self.base_url, next_page_relative_url)
            response = self._get_page(url=next_page_url)

            # append page results
            results.append(self._parse_other_page(response=response))

            # update index
            soup = BeautifulSoup(response.text, "lxml")
            spans = soup.select("thead span.goto")
            i = next(
                (
                    i
                    for i, span in enumerate(spans)
                    if not span.select_one("a").has_attr("href")
                ),
                None,
            )

        df = pd.concat(results, ignore_index=True) if results else pd.DataFrame()
        return df

    def search(
        self, search_string: str, period_from: str, extensive: bool = False
    ) -> pd.DataFrame:
        results = []
        response = self._get_first_page(
            search_string=search_string, period_from=period_from
        )
        df: pd.DataFrame = self._parse_first_page(response=response)
        if extensive:
            others_df: pd.DataFrame = self._get_other_pages(response=response)

            results.extend([df, others_df])
            df = pd.concat(results, ignore_index=True)
        return df

    def _parse_table(self, html: str):
        soup = BeautifulSoup(html, "lxml")

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
                relative_url = a_tag.get("href", "")
                full_link = urljoin(self.base_url, relative_url)

            row = []
            row.append(title)
            row.append(full_link)
            row.extend([cell.get_text(separator=" ", strip=True) for cell in cells[1:]])

            if len(row) == len(headers):
                data_rows.append(row)

        df = pd.DataFrame(data_rows, columns=headers)
        return df

    def _parse_first_page(self, response: requests.Response) -> pd.DataFrame:
        text = response.text
        return self._parse_table(text)

    def _parse_other_page(self, response: requests.Response) -> pd.DataFrame:
        text = response.text
        soup = BeautifulSoup(text, "xml")
        component_tag = soup.find("component")
        cdata_content = component_tag.contents[0]
        return self._parse_table(cdata_content)
