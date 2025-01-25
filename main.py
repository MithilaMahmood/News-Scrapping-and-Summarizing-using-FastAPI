from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from summarizing import router as summarize_router
from db_connection import connect_database
import os
from dotenv import load_dotenv

load_dotenv()
print("Loaded GROQ_API_KEY:", os.getenv("GROQ_API_KEY")) 

# Lifespan function to manage startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = connect_database()
    if conn:
        print("Database connected successfully.")
        conn.close()
    else:
        print("Failed to connect to the database.")
    yield  # Allow app to run
    # You can add cleanup logic here if needed

# Initialize FastAPI app
app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(summarize_router)

# Pydantic model for News Item
class NewsItem(BaseModel):
    id: int
    category: str
    title: str
    link: str
    image_url: str
    content: str
class NewsSummary(BaseModel):
    news_id: int
    summary_text: str    

# API to fetch all news
@app.get("/news", response_model=list[NewsItem])
def get_all_news():
    conn = connect_database()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed.")
        
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, category, title, link, image_url, content FROM news_ta ORDER BY id DESC")
        results = cursor.fetchall()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching news:{str(e)}")
    finally:
        cursor.close()
        conn.close()
    

# API to fetch news by category
@app.get("/news/category/{category}", response_model=list[NewsItem])
def get_news_by_category(category: str):
    conn = connect_database()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT * FROM news_ta WHERE category = %s ORDER BY id DESC"
            cursor.execute(query, (category,))
            results = cursor.fetchall()
            return results
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching news by category: {e}")
        finally:
            cursor.close()
            conn.close()
    else:
        raise HTTPException(status_code=500, detail="Database connection failed.")

# API to fetch a single news item by ID
@app.get("/news/{news_id}", response_model=NewsItem)
def get_news_by_id(news_id: int):
    conn = connect_database()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT * FROM news_ta WHERE id = %s"
            cursor.execute(query, (news_id,))
            result = cursor.fetchone()
            if result:
                return result
            else:
                raise HTTPException(status_code=404, detail="News item not found.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching news item: {e}")
        finally:
            cursor.close()
            conn.close()
    else:
        raise HTTPException(status_code=500, detail="Database connection failed.")

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the News Summarization API"}


