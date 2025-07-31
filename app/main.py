import warnings

import pandas as pd
from bs4.builder import XMLParsedAsHTMLWarning
from search import EvergabeSearcher
from utils import get_date_one_month_from_now

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

search_keywords = [
    {"en": "artificial intelligence", "de": "künstliche intelligenz"},
    {"en": "data platforms", "de": "Datenplattformen"},
    {"en": "AI platforms", "de": "KI-Plattformen"},
    {"en": "chatbots", "de": "Chatbots"},
    {"en": "multi agents", "de": "Multi-Agenten"},
    {"en": "generative AI", "de": "generative KI"},
    {"en": "machine learning", "de": "maschinelles Lernen"},
    {"en": "deep learning", "de": "Deep Learning"},
    {"en": "natural language processing", "de": "Verarbeitung natürlicher Sprache"},
    {"en": "knowledge graph", "de": "Wissensgraph"},
    {"en": "data pipeline", "de": "Datenpipeline"},
    {"en": "cloud", "de": "Cloud"},
    {"en": "conversational AI", "de": "Konversations-KI"},
    {"en": "data engineering", "de": "Datenengineering"},
    {"en": "data science", "de": "Datenwissenschaft"},
    {"en": "RAG", "de": "RAG"},
    {
        "en": "Retrieval Augmented Generation",
        "de": "Retrieval Augmentierte Generierung",
    },
    {"en": "Large Language Model", "de": "Großes Sprachmodell"},
    {"en": "transformers", "de": "Transformer"},
    {"en": "big data", "de": "Big Data"},
]


def main(extensive: bool = False):
    searcher = EvergabeSearcher()

    period_from = get_date_one_month_from_now()
    all_results = []

    for keyword_dict in search_keywords:
        keyword_en, keyword_de = keyword_dict.values()
        print(f"Searching '{keyword_en}'...")
        en_df = searcher.search(
            search_string=keyword_en, period_from=period_from, extensive=extensive
        )
        print(f"Searching '{keyword_de}'...")
        de_df = searcher.search(
            search_string=keyword_de, period_from=period_from, extensive=extensive
        )

        all_results.append(en_df)
        all_results.append(de_df)

    df = pd.concat(all_results, ignore_index=True)
    df = df.drop_duplicates(subset="Geschäftszeichen")

    df.to_html("res/results.html")
    print("Saved response to 'results.html'")


if __name__ == "__main__":
    main()
