import requests

API_KEY = "350adfc422324a1e8fcc53131da18548"
BASE_URL = "https://newsapi.org/v2/everything"

CATEGORY_KEYWORDS = {
    "general": "latest news",
    "sports": "sports cricket football",
    "technology": "technology AI software",
    "entertainment": "movies music celebrities",
    "health": "health fitness medicine",
    "business": "business finance economy",
    "science": "science research innovation"
}


def get_news(search_query, page=1, page_size=10):
    params = {
        "apiKey": API_KEY,
        "q": search_query,
        "language": "en",
        "sortBy": "publishedAt",
        "page": page,
        "pageSize": page_size
    }

    response = requests.get(BASE_URL, params=params)
    data = response.json()

    articles = []

    if data.get("status") == "ok":
        for item in data.get("articles", []):
            articles.append({
                "title": item.get("title"),
                "description": item.get("description"),
                "url": item.get("url"),
                "image": item.get("urlToImage"),
                "category": search_query
            })

    return articles


