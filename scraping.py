from bs4 import BeautifulSoup 
import requests
import re
from db_connection import connect_database, create_table, add_columns_if_not_exists, store_news, remove_duplicates,execute_sql_file

def scrape_news(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")

    # Find the main container using your provided selector
    main_container = soup.select_one("#__layout > div > main")
    
    if not main_container:
        print("Main container not found.")
        return []

    news_data = []
    for article in main_container.find_all("article"):
        news_item = {}
        
        # Scrape the category
        try:
            category_tag = article.find("a")  # Adjust this selector based on your HTML
            news_item["category"] = category_tag.text.strip() if category_tag else None
        except AttributeError:
            news_item["category"] = None

        try:
            title_tag = article.find("h2") or article.find("h3")
            news_item["title"] = title_tag.text.strip()
        except AttributeError:
            news_item["title"] = None

        try:
            link_tag = article.find("a")
            news_item["link"] = link_tag["href"]
        except (AttributeError, KeyError):
            news_item["link"] = None

        try:
            image_tag = article.find("img")
            news_item["image_url"] = image_tag["src"] if image_tag else None
        except KeyError:
            news_item["image_url"] = None

        try:
            details_tag = article.find("p")
            details_text = details_tag.get_text(separator="\n").strip()
            news_item["content"] = re.sub(r"\s+", " ", details_text)
        except AttributeError:
            news_item["content"] = None

        news_data.append(news_item)

    return news_data


if __name__ == "__main__":
    # Run the SQL file (optional)
    execute_sql_file('mysql_connection.sql')  # Replace with your actual .sql file path

    # Scrape the website and store data in the database
    website_url = "https://thefinancialexpress.com.bd/page/stock/bangladesh"
    news_data = scrape_news(website_url)
    
    conn = connect_database()
    if conn:
        create_table()
        add_columns_if_not_exists()

        for item in news_data:
            store_news(conn, item)
        remove_duplicates()
        conn.close()
        print("All data stored in database, and duplicates removed.")
    else:
        print("Error connecting to database.")
