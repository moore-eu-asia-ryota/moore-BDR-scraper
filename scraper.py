import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from dateutil import parser
import datetime

# Constants
BASE_URL = 'https://www.moore-bdr.sk'
NEWS_URL = f'{BASE_URL}/novinky/'
COMPANY_NAME = "Moore BDR"

def fetch_page(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def parse_main_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    # Find year tabs (assuming they are <a> tags with the year text)
    year_tabs = soup.select('a.ui-tabs-anchor')
    years = {}
    for tab in year_tabs:
        year = tab.get_text(strip=True)
        # The href attribute holds an anchor that might be used to identify which section to parse.
        anchor = tab.get('href')
        years[year] = anchor
    return years

def parse_news_entries(soup):
    # Adjust the selector based on the HTML structure
    # Example: find all div elements with class "post-entry-content"
    entries = soup.find_all('div', class_='post-entry-content')
    news_items = []
    for entry in entries:
        title_element = entry.find('h3', class_='entry-title')
        if title_element and title_element.find('a'):
            title = title_element.find('a').get_text(strip=True)
            link = title_element.find('a').get('href')
        else:
            continue

        # Published date
        date_element = entry.find('time', class_='entry-date')
        if date_element:
            raw_date = date_element.get_text(strip=True)
            # Parse date using dateutil; assuming the text is something like "13.január 2025"
            try:
                # Some locales might require adjustments, so if needed manually map month names.
                dt = parser.parse(raw_date, fuzzy=True)
            except Exception:
                dt = datetime.datetime.now()
            # Format date as mm/dd/yyyy
            pub_date = dt.strftime('%m/%d/%Y')
        else:
            pub_date = ""

        # Get excerpt (if available)
        excerpt_element = entry.find('div', class_='entry-excerpt')
        excerpt = excerpt_element.get_text(strip=True) if excerpt_element else ""

        # Get full article content by visiting the page
        content = fetch_article_content(link)

        news_items.append({
            'title': title,
            'pub_date': pub_date,
            'content': content,
            'source': COMPANY_NAME,
            'link': link,
            'excerpt': excerpt
        })
    return news_items

def fetch_article_content(url):
    try:
        html = fetch_page(url)
        soup = BeautifulSoup(html, 'html.parser')
        # Adjust the selector based on the structure of the individual article page
        content_div = soup.find('div', class_='post-entry-content')
        if content_div:
            return content_div.get_text(strip=True)
    except Exception as e:
        print(f"Error fetching article content from {url}: {e}")
    return ""

def generate_rss_feed(news_items):
    fg = FeedGenerator()
    fg.title("Moore BDR News")
    fg.link(href=NEWS_URL, rel='alternate')
    fg.description("RSS feed for news from Moore BDR")
    fg.language("sk")

    for item in news_items:
        fe = fg.add_entry()
        fe.title(item['title'])
        fe.link(href=item['link'])
        fe.pubDate(item['pub_date'])
        # Use the article content; you can also append the excerpt if desired.
        fe.description(item['content'])
        fe.author({'name': item['source']})
    return fg.rss_str(pretty=True)

def main():
    # Fetch the main news page
    main_html = fetch_page(NEWS_URL)
    soup = BeautifulSoup(main_html, 'html.parser')

    # You can optionally parse and iterate over different year tabs if the content is segmented.
    # For simplicity, we assume all news are loaded in the main page or can be navigated accordingly.
    news_items = parse_news_entries(soup)

    # Generate RSS feed
    rss_feed = generate_rss_feed(news_items)

    # Write RSS feed to file
    with open('rss.xml', 'wb') as f:
        f.write(rss_feed)
    print("RSS feed generated and saved as rss.xml")

if __name__ == "__main__":
    main()
