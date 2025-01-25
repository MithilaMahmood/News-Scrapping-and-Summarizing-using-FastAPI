import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database configuration from environment variables
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASS'),
    'database': os.getenv('DB_NAME')
}

# Connect to the database
def connect_database():
    try:
        # Connect to MySQL without specifying a database
        conn = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password']
        )
        cursor = conn.cursor()

        # Create the database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS news_db")
        conn.commit()

        # Now connect to the `news_db` database
        conn.close()
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as e:
        print(f"Error connecting to database: {e}")
        return None
    

# Create table (if not exists)
def create_table():
    try:
        conn = connect_database()
        if conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS news_ta (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    category TEXT,       
                    title TEXT NOT NULL,
                    link TEXT,
                    image_url TEXT,
                    content TEXT,              
                    UNIQUE (title(255), link(255)) -- Specify key length for TEXT columns
                )
            ''')
            # Create `summaries` table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS summaries (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    news_id INT NOT NULL,
                    summary_text TEXT,
                    FOREIGN KEY (news_id) REFERENCES news_ta (id) ON DELETE CASCADE
                )
            ''')
            conn.commit()
            conn.close()
            print("Table created successfully.")
    except mysql.connector.Error as e:
        print(f"Error creating table: {e}")

def add_columns_if_not_exists():
    try:
        conn = connect_database()
        if conn:
            cursor = conn.cursor()

            # Check if the 'category' column exists, and add it if it doesn't
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'news_ta' AND COLUMN_NAME = 'category'
            """, (db_config['database'],))
            if cursor.fetchone()[0] == 0:
                cursor.execute('ALTER TABLE news_ta ADD COLUMN category TEXT')
                print("Added 'category' column.")

            conn.commit()
            conn.close()
            print("Checked and added missing columns successfully.")
    except mysql.connector.Error as e:
        print(f"Error adding columns: {e}")


# Store news in the database
def store_news(conn, news_item):
    try:
        cursor = conn.cursor()
        query = '''
            INSERT INTO news_ta (category, title, link, image_url, content)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                category = VALUES(category),
                link = VALUES(link),
                image_url = VALUES(image_url),
                content = VALUES(content)
                
        '''
        data = (
            news_item["category"],
            news_item["title"],
            news_item["link"],
            news_item["image_url"],
            news_item["content"],
            
        )
   

        cursor.execute(query, data)
        conn.commit()
    except mysql.connector.Error as e:
        print(f"Error storing news item: {e}")
    finally:
        cursor.close()

# Remove duplicates from the database
def remove_duplicates():
    try:
        conn = connect_database()
        if conn:
            cursor = conn.cursor()

            # Create a temporary table to store unique rows
            cursor.execute('''
                CREATE TEMPORARY TABLE temp_news AS
                SELECT MIN(id) AS id
                FROM news_ta
                GROUP BY
                    TRIM(LOWER(title)),  -- Trim and convert title to lowercase for comparison
                    TRIM(LOWER(link))    -- Trim and convert link to lowercase for comparison
            ''')

            # Delete rows not in the temporary table
            cursor.execute('''
                DELETE FROM news_ta
                WHERE id NOT IN (
                    SELECT id FROM temp_news
                )
            ''')

            conn.commit()
            print("Duplicates removed successfully.")
            conn.close()
    except mysql.connector.Error as e:
        print(f"Error removing duplicates: {e}")

# Execute an SQL file
def execute_sql_file(sql_file_path):
    try:
        conn = connect_database()
        if conn:
            cursor = conn.cursor()

            # Read the SQL file content
            with open(sql_file_path, 'r') as file:
                sql_commands = file.read()

            # Execute SQL commands split by semicolon
            for command in sql_commands.split(';'):
                if command.strip():
                    cursor.execute(command.strip())
                    # Fetch or discard all results to prevent "Unread result found"
                    cursor.fetchall() if cursor.with_rows else None

            conn.commit()
            conn.close()
            print(f"SQL file '{sql_file_path}' executed successfully.")
    except mysql.connector.Error as e:
        print(f"Error executing SQL file: {e}")
    except FileNotFoundError:
        print(f"SQL file '{sql_file_path}' not found.")