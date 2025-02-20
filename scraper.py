import requests
from bs4 import BeautifulSoup
from dateutil import parser
from datetime import timezone
from feedgen.feed import FeedGenerator

def fetch_news_items(url):
    """
    Scrapes the main news page and extracts a list of news items.
    Each news item is expected to have:
      - Title and link in an <h3 class="entry-title"><a ...> element
      - Publication date in a <time class="entry-date updated" datetime="..."> element
    """
    response = requests.get(url)
    response.raise_for_status()  # Raise error if request fails
    soup = BeautifulSoup(response.text, 'html.parser')
    
    news_items = []
    # Adjust the selector as needed for the structure of your page
    # Here we assume each news item is contained in a div with class "post-entry-content"
    entries = soup.find_all('div', class_='post-entry-content')
    
    for entry in entries:
        # Get the title and link
        h3 = entry.find('h3', class_='entry-title')
        if not h3:
            continue  # skip if title not found
        a_tag = h3.find('a')
        title = a_tag.get_text(strip=True)
        link = a_tag['href']
        
        # Get the publication date from the <time> element
        time_tag = entry.find('time', class_='entry-date updated')
        if time_tag and time_tag.has_attr('datetime'):
            # Parse the ISO datetime string (e.g., "2025-01-13T17:18:00+00:00")
            pub_date = parser.parse(time_tag['datetime'])
        else:
            # If no date is found, you might choose to skip or use the current time
            pub_date = None
        
        # Only include items with a publication date
        if pub_date:
            news_items.append({
                'title': title,
                'link': link,
                'pub_date': pub_date,
            })
    return news_items

def generate_rss_feed(news_items):
    """
    Generates an RSS feed using the Feedgen library.
    """
    fg = FeedGenerator()
    fg.title('Moore BDR News Feed')
    fg.link(href='https://www.moore-bdr.sk/novinky/', rel='alternate')
    fg.description('Latest news from Moore BDR')
    
    for item in news_items:
        fe = fg.add_entry()
        fe.title(item['title'])
        fe.link(href=item['link'])
        
        # Ensure that the publication date is timezone-aware.
        # In this case, our parser should return an aware datetime
        pub_date = item['pub_date']
        if pub_date.tzinfo is None:
            pub_date = pub_date.replace(tzinfo=timezone.utc)
        fe.pubDate(pub_date)
    
    return fg.rss_str(pretty=True)

def main():
    url = 'https://www.moore-bdr.sk/novinky/'
    news_items = fetch_news_items(url)
    rss_feed = generate_rss_feed(news_items)
    
    # Save the RSS feed as XML and also copy it to a text file if needed.
    with open('feed.xml', 'wb') as f:
        f.write(rss_feed)
    
    # If you want to have a plain text version as well:
    with open('feed.txt', 'w', encoding='utf-8') as f:
        f.write(rss_feed.decode('utf-8'))
    
    print("RSS feed generated and saved as 'feed.xml' and 'feed.txt'.")

if __name__ == '__main__':
    main()
