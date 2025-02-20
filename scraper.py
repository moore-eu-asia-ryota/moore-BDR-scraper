import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from dateutil import parser
import datetime
import os

# Constants
BASE_URL = 'https://www.moore-bdr.sk'
NEWS_URL = f'{BASE_URL}/novinky/'
COMPANY_NAME = "Moore BDR"

def fetch_page(url):
    """Fetch HTML from the given URL and return it as text."""
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def parse_news_entries(soup):
    """
    Parse the main listing page (the /novinky/ page) to find each article entry.
    Return a list of dictionaries with partial info (link, date, etc.).
    """
    entries = soup.find_all('div', class_='post-entry-content')
    news_items = []

    for entry in entries:
        # Title/link from the listing (though we will re-check the <h1> on the article page)
        title_element = entry.find('h3', class_='entry-title')
        if title_element and title_element.find('a'):
            link = title_element.find('a').get('href')
        else:
            continue

        # Published date from the listing
        date_element = entry.find('time', class_='entry-date')
        if date_element:
            raw_date = date_element.get_text(strip=True)
            try:
                dt = parser.parse(raw_date, fuzzy=True)
            except Exception:
                dt = datetime.datetime.now()
            pub_date = dt.strftime('%m/%d/%Y')
        else:
            pub_date = ""

        # Optional excerpt
        excerpt_element = entry.find('div', class_='entry-excerpt')
        excerpt = excerpt_element.get_text(strip=True) if excerpt_element else ""

        news_items.append({
            'listing_pub_date': pub_date,
            'listing_excerpt': excerpt,
            'link': link
        })

    return news_items

def fetch_article_details(article_url):
    """
    Visit the individual article page to extract:
    - The H1 title (entry-title)
    - The main content from <div class="wpb_wrapper">
    """
    try:
        html = fetch_page(article_url)
        soup = BeautifulSoup(html, 'html.parser')

        # 1. Extract the H1 title
        h1_element = soup.find('h1', class_='entry-title')
        if h1_element:
            title = h1_element.get_text(strip=True)
        else:
            title = "Untitled"

        # 2. Extract the main content from <div class="wpb_wrapper">
        content_div = soup.find('div', class_='wpb_wrapper')
        if content_div:
            # Collect text from each child element
            content_parts = []
            for child in content_div.children:
                # Only extract text from actual elements
                if child.name:
                    part = child.get_text(strip=True)
                    if part:
                        content_parts.append(part)
            full_content = "\n".join(content_parts)
        else:
            full_content = ""

        return title, full_content
    except Exception as e:
        print(f"Error fetching article content from {article_url}: {e}")
        return "Untitled", ""

def generate_rss_feed(news_items):
    """
    Generate an RSS feed string from a list of news items.
    """
    fg = FeedGenerator()
    fg.title("Moore BDR News")
    fg.link(href=NEWS_URL, rel='alternate')
    fg.description("RSS feed for news from Moore BDR")
    fg.language("sk")

    for item in news_items:
        fe = fg.add_entry()
        fe.title(item['title'])            # The final H1-based title
        fe.link(href=item['link'])
        fe.pubDate(item['pub_date'])
        fe.description(item['content'])    # The full text content
        fe.author({'name': item['source']})
    return fg.rss_str(pretty=True)

def main():
    # 1. Fetch the main /novinky/ page
    main_html = fetch_page(NEWS_URL)
    soup = BeautifulSoup(main_html, 'html.parser')

    # 2. Parse the listing to get links and partial data
    listing_items = parse_news_entries(soup)
    final_news_items = []

    # 3. Clear or create a single text file to store all articles
    #    We'll overwrite it each time the script runs.
    articles_filename = 'articles.txt'
    if os.path.exists(articles_filename):
        os.remove(articles_filename)

    # 4. Fetch details from each individual article
    for item in listing_items:
        link = item['link']
        article_title, article_content = fetch_article_details(link)

        # Compose a final dictionary with all required info
        news_dict = {
            'title': article_title,
            'pub_date': item['listing_pub_date'],
            'content': article_content,
            'source': COMPANY_NAME,
            'link': link
        }

        # 5. Append the article’s content to the single text file
        with open(articles_filename, 'a', encoding='utf-8') as f:
            f.write(f"Title: {news_dict['title']}\n")
            f.write(f"Date: {news_dict['pub_date']}\n")
            f.write(f"Link: {news_dict['link']}\n")
            f.write(f"Source: {news_dict['source']}\n")
            f.write("Content:\n")
            f.write(news_dict['content'] + "\n")
            f.write("=" * 80 + "\n\n")

        final_news_items.append(news_dict)

    # 6. Generate RSS feed from the collected data
    rss_feed = generate_rss_feed(final_news_items)

    # 7. Write the RSS feed to rss.xml
    with open('rss.xml', 'wb') as f:
        f.write(rss_feed)

    print("RSS feed generated and saved as rss.xml")
    print(f"All article contents appended to {articles_filename}")

if __name__ == "__main__":
    main()
