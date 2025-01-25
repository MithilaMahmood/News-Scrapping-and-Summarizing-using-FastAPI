from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db_connection import connect_database
from utility import generate_summary

router = APIRouter(
    prefix="/summaries",
    tags=["summaries"],
)

# Pydantic model for Summary
class Summary(BaseModel):
    id: int
    news_id: int
    summary_text: str

# API to generate and store a summary for a specific news item
@router.post("/", response_model=Summary)
def create_summary(news_id: int):
    conn = connect_database()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed.")
    
    cursor = conn.cursor(dictionary=True)
    try:
        # Fetch the content of the news item by ID
        query = "SELECT id, content FROM news_ta WHERE id = %s"
        cursor.execute(query, (news_id,))
        news_item = cursor.fetchone()
        
        if not news_item:
            raise HTTPException(status_code=404, detail="News item not found.")
        
        # Generate the summary using the Llama model
        news_body = news_item["content"]
        summary_text = generate_summary(news_body)
        
        # Store the summary in the database
        insert_query = '''
            INSERT INTO summaries (news_id, summary_text)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                summary_text = VALUES(summary_text)
        '''
        cursor.execute(insert_query, (news_item["id"], summary_text))
        conn.commit()
        
        return {"id": cursor.lastrowid, "news_id": news_item["id"], "summary_text": summary_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating summary: {e}")
    finally:
        cursor.close()
        conn.close()

# API to fetch a summary by summary ID
@router.get("/{summary_id}", response_model=Summary)
def get_summary(summary_id: int):
    conn = connect_database()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed.")
    
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT * FROM summaries WHERE id = %s"
        cursor.execute(query, (summary_id,))
        summary = cursor.fetchone()
        
        if not summary:
            raise HTTPException(status_code=404, detail="Summary not found.")
        
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching summary: {e}")
    finally:
        cursor.close()
        conn.close()
