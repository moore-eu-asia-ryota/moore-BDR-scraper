#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import datetime
import os
from feedgen.feed import FeedGenerator

# --- Define functions to scrape main page and individual articles ---

def scrape_main_page(url):
    """Scrape the main page to get a list of news items."""
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    news_items = []
    # For each news item block on the main page...
    for item in soup.select('.post-entry-content'):
        # Extract title and link from the h3 > a element
        title_elem = item.select_one("h3.entry-title a")
        if title_elem:
            title = title_elem.get_text(strip=True)
            link = title_elem['href']
        else:
            continue

        # Extract publish date from the <time> element
        time_elem = item.select_one("time.entry-date")
        if time_elem and time_elem.has_attr("datetime"):
            # Parse the datetime string including timezone info.
            pub_date = datetime.datetime.fromisoformat(time_elem['datetime'])
        else:
            pub_date = None

        news_items.append({
            'title': title,
            'link': link,
            'pub_date': pub_date
        })
    return news_items

def scrape_article_content(url):
    """Scrape an individual article page to extract its content."""
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    # Assuming main content is in an element with class 'entry-content'
    content_elem = soup.select_one('.entry-content')
    if content_elem:
        return content_elem.get_text(strip=True)
    return ""

def generate_rss_feed(news_items):
    """Generate RSS feed XML from the list of news items."""
    fg = FeedGenerator()
    fg.title("Moore BDR News")
    fg.link(href="https://www.moore-bdr.sk/novinky/", rel="alternate")
    fg.description("Latest news from Moore BDR s.r.o.")
    fg.language("sk")

    for item in news_items:
        fe = fg.add_entry()
        fe.title(item['title'])
        fe.link(href=item['link'])
        # Make sure the datetime object has timezone info.
        if item['pub_date'] is None:
            continue  # Skip if no pub_date
        if item['pub_date'].tzinfo is None:
            # If there's no timezone, assume UTC (or adjust as needed)
            item['pub_date'] = item['pub_date'].replace(tzinfo=datetime.timezone.utc)
        fe.pubDate(item['pub_date'])
        # Fetch the content from the individual article page
        content = scrape_article_content(item['link'])
        fe.description(content)

    return fg.rss_str(pretty=True).decode('utf-8')

def main():
    base_url = "https://www.moore-bdr.sk/novinky/"
    # You might have logic to go through year tabs etc.
    # For simplicity, we'll assume base_url lists all news.
    news_items = scrape_main_page(base_url)
    # Here you could loop over tabs/years if needed

    # Generate the RSS feed XML
    rss_feed = generate_rss_feed(news_items)

    # Write the RSS feed to a file in the repository root
    output_path = os.path.join(os.getcwd(), "rss.xml")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rss_feed)
    print("RSS feed written to:", output_path)
    # Debug: list current directory contents
    print("Files in current directory:", os.listdir(os.getcwd()))

if __name__ == "__main__":
    main()
