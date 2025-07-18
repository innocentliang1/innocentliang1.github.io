from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from utils.logger import log_event
from email.mime.text import MIMEText
from email.utils import formatdate
import smtplib
import os
import pandas as pd
from datetime import datetime, timedelta
import os
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from openai import OpenAI
import uuid
import requests
from PIL import Image
from io import BytesIO
import base64
import time

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Chinese Name & Signature Generator")

# Configure templates
templates = Jinja2Templates(directory="templates")

# Create directories for static files and signatures
os.makedirs("static", exist_ok=True)
os.makedirs("static/signatures", exist_ok=True)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Silicon Flow API client
client = OpenAI(
    api_key=os.getenv("SILICON_FLOW_API_KEY"),
    base_url=os.getenv("SILICON_FLOW_BASE_URL")
)

# Initialize DashScope API for image generation
dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")

# Data models
class NameRequest(BaseModel):
    foreign_name: str

class SignatureRequest(BaseModel):
    chinese_name: str

class SharedName(BaseModel):
    id: str
    foreign_name: str
    chinese_name: str
    pinyin: str
    explanation: str

# In-memory storage for shared names (in production, use a database)
shared_names = {}

# Track donation button clicks
donation_clicks = {
    "total": 0,
    "last_click_time": None
}

# Routes

@app.post("/track_donation_click")
async def track_donation_click():
    """Track when donation button is clicked"""
    donation_clicks["total"] += 1
    donation_clicks["last_click_time"] = time.time()
    return {"status": "success", "total_clicks": donation_clicks["total"]}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    client_ip = request.client.host
    log_event("page_visit", ip=client_ip, page="/")
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate-name")
async def generate_name(foreign_name: str = Form(...)):
    try:
        # Prompt engineering for Chinese name generation with cultural context
        prompt = f"""
        Task: Generate an authentic Chinese name for a foreigner with the name '{foreign_name}'
        Requirements:
        1. The name must be a genuine Chinese name with 2-3 Chinese characters, NOT a transliteration of the foreign name
        2. Each character should have positive meanings and cultural connotations
        3. The name should sound pleasant in Chinese pronunciation
        4. Provide Pinyin pronunciation with tone marks
        5. Explain the meaning of each character and the overall cultural significance
        6. Include references to Chinese culture, philosophy, or classical literature if relevant
        7. Format the response as a JSON object with keys: chinese_name, pinyin, explanation
        8. Write explanation in elegant English with cultural depth
        Important: Avoid using characters that only approximate the sound of the foreign name; focus on meaningful Chinese character combinations that would be used as real names by Chinese people.
        """

        # Call Silicon Flow API
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=[
                {'role': 'system', 'content': 'You are a Chinese naming expert with deep knowledge of classical Chinese literature and philosophy.'},
                {'role': 'user', 'content': prompt}
            ]
        )

        # Log API response for debugging
        raw_response = response.choices[0].message.content
        print(f"API Response: {raw_response}")
        
        # Parse the JSON response
        import json
        try:
            result = json.loads(raw_response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks if present
            import re
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', raw_response)
            if json_match:
                try:
                    result = json.loads(json_match.group(1))
                except json.JSONDecodeError as e:
                    raise HTTPException(status_code=500, detail=f"JSON parsing failed: {str(e)}")
            else:
                raise HTTPException(status_code=500, detail=f"Invalid response format: {raw_response}")
        
        # Validate response structure
        required_fields = ['chinese_name', 'pinyin', 'explanation']
        if not all(field in result for field in required_fields):
            raise HTTPException(status_code=500, detail=f"API response missing required fields: {required_fields}")
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating Chinese name: {str(e)}")

@app.post("/share-name")
async def share_name(name_data: dict):
    """Create a shareable link for a generated name"""
    try:
        # Validate required fields
        required_fields = ['foreign_name', 'chinese_name', 'pinyin', 'explanation']
        if not all(field in name_data for field in required_fields):
            raise HTTPException(status_code=400, detail=f"Missing required fields: {required_fields}")
        
        # Generate unique ID and store data
        share_id = str(uuid.uuid4())
        shared_names[share_id] = name_data
        
        return {
            "share_id": share_id,
            "share_url": f"/shared-name/{share_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating share link: {str(e)}")

@app.get("/shared-name/{share_id}")
async def get_shared_name(share_id: str, request: Request, preview: bool = False):
    """Retrieve shared name data by ID"""
    try:
        if share_id not in shared_names:
            raise HTTPException(status_code=404, detail="Shared name not found")
        
        # Always return HTML when accessed via browser
        if preview or "text/html" in request.headers.get("accept", ""):
            name_data = shared_names[share_id]
            return templates.TemplateResponse(
                "shared_name.html",
                {
                    "request": request,
                    "name_data": name_data,
                    "foreign_name": name_data["foreign_name"],
                    "chinese_name": name_data["chinese_name"],
                    "pinyin": name_data["pinyin"],
                    "explanation": name_data["explanation"]
                }
            )
        
        # Redirect to HTML version for direct API access
        redirect_url = request.url_for("get_shared_name", share_id=share_id)
        return RedirectResponse(url=f"{redirect_url}?preview=true")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving shared name: {str(e)}")

# 确保签名存储目录存在
os.makedirs("static/signatures", exist_ok=True)

@app.get("/download-signature/{signature_id}")
async def download_signature(signature_id: str):
    """Download signature image"""
    signature_file = f"static/signatures/{signature_id}.png"
    if not os.path.exists(signature_file):
        raise HTTPException(status_code=404, detail="Signature not found")
    return FileResponse(
        signature_file, 
        filename=f"signature_{signature_id}.png",
        media_type="image/png"
    )

@app.get("/export-logs")
async def export_logs(request: Request, days: int = 7):
    """Export logs to Excel file"""
    client_ip = request.client.host
    log_event("log_export_request", ip=client_ip, days=days)
    
    try:
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Get log files within date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        log_files = []
        
        for day in range(days + 1):
            date = start_date + timedelta(days=day)
            log_file = f"logs/app.log.{date.strftime('%Y-%m-%d')}"
            if os.path.exists(log_file):
                log_files.append(log_file)
        
        # Read and parse log files
        log_data = []
        for file in log_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            # Parse log line (simplified example)
                            time_part, level_part, json_part = line.split(' | ', 2)
                            log_entry = eval(json_part)  # Simple way to parse the dict
                            log_entry['timestamp'] = time_part
                            log_entry['level'] = level_part
                            log_data.append(log_entry)
                        except:
                            continue
            except Exception as e:
                continue
        
        if not log_data:
            raise HTTPException(status_code=404, detail="No log data found for the specified period")
        
        # Create DataFrame and export to Excel
        df = pd.DataFrame(log_data)
        excel_file = f"logs/export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(excel_file, index=False)
        
        log_event("log_export_success", ip=client_ip, file=excel_file)
        return FileResponse(excel_file, filename=f"logs_export.xlsx")
    
    except HTTPException:
        raise
    except Exception as e:
        log_event("log_export_error", ip=client_ip, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to export logs: {str(e)}")

@app.post("/generate-signature")
async def generate_signature(chinese_name: str = Form(...), request: Request = None):
    """Generate artistic Chinese signature for a given name"""
    client_ip = request.client.host if request else "unknown"
    log_event("signature_request_start", ip=client_ip, name=chinese_name)
    
    if not dashscope_api_key:
        log_event("signature_error", ip=client_ip, error="DashScope API key not configured")
        raise HTTPException(status_code=500, detail="DashScope API key not configured")
    
    if not chinese_name:
        log_event("signature_error", ip=client_ip, error="Chinese name is required")
        raise HTTPException(status_code=400, detail="Chinese name is required")
    
    # Generate signature using DashScope API
    prompt = f"Professional Chinese calligraphy signature for the name '{chinese_name}'. "
    prompt += "Elegant and artistic style with smooth brush strokes. "
    prompt += "Black ink on white background. High resolution and clear."
    
    try:
        from dashscope import ImageSynthesis
        from urllib.parse import urlparse, unquote
        from pathlib import PurePosixPath
        from http import HTTPStatus
        
        rsp = ImageSynthesis.call(
            api_key=dashscope_api_key,
            model="wanx2.1-t2i-turbo",
            prompt=prompt,
            n=1,
            size='1024*1024'
        )
        
        if rsp.status_code != HTTPStatus.OK:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate signature: {rsp.message}"
            )
            
        # Save the signature image with .png extension
        os.makedirs("static/signatures", exist_ok=True)
        result = rsp.output.results[0]
        signature_id = str(uuid.uuid4()) + str(int(time.time()))
        save_path = f"static/signatures/{signature_id}.png"
        
        # Download and save the image
        image_data = requests.get(result.url).content
        with open(save_path, 'wb+') as f:
            f.write(image_data)
        
        # Log successful signature generation
        log_event("signature_generated", 
                ip=client_ip, 
                name=chinese_name,
                signature_id=signature_id)
        
        # Log image saved
        log_event("signature_image_saved",
                ip=client_ip,
                signature_id=signature_id,
                file_path=save_path)
            
        return {
            "signature_url": f"/static/signatures/{signature_id}.png",
            "signature_id": signature_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating signature: {str(e)}"
        )

@app.post("/submit-feedback")
async def submit_feedback(request: Request):
    """Handle feedback submission and send email"""
    try:
        form_data = await request.form()
        message = form_data.get("message")
        if not message:
            raise HTTPException(
                status_code=400,
                detail="Message is required"
            )
            
        client_ip = request.client.host
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create email message
        msg = MIMEText(f"""
        Feedback Received:
        
        Time: {timestamp}
        IP Address: {client_ip}
        
        Message:
        {message}
        """)
        
        msg['Subject'] = f"Website Feedback from {client_ip}"
        msg['From'] = os.getenv("SMTP_USERNAME")
        msg['To'] = os.getenv("EMAIL_RECEIVER")
        msg['Date'] = formatdate(localtime=True)
        
        # Log SMTP configuration for debugging
        smtp_config = {
            "server": os.getenv("SMTP_SERVER"),
            "port": os.getenv("SMTP_PORT"),
            "username": os.getenv("SMTP_USERNAME"),
            "receiver": os.getenv("EMAIL_RECEIVER")
        }
        log_event("smtp_config", ip=client_ip, config=smtp_config)
        
        # Create SMTP connection with timeout
        server = smtplib.SMTP_SSL(
            host=os.getenv("SMTP_SERVER"),
            port=int(os.getenv("SMTP_PORT")),
            timeout=10
        )
        server.set_debuglevel(1)  # Enable verbose debug output
        
        try:
            # Authenticate
            server.login(
                user=os.getenv("SMTP_USERNAME"),
                password=os.getenv("SMTP_PASSWORD")
            )
            
            # Send message (critical operation)
            server.send_message(msg)
            
            # Log successful email sending
            log_event("email_sent_success", ip=client_ip)
            
            # Log feedback submission
            log_event("feedback_submitted", 
                     ip=client_ip,
                     message_length=len(message))
            
            return {"status": "success", "message": "Feedback submitted successfully"}
            
        except Exception as e:
            log_event("feedback_error", 
                     ip=client_ip,
                     error=str(e))
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process feedback: {str(e)}"
            )
        finally:
            try:
                # Non-critical operation - ignore QUIT errors
                server.quit()
            except:
                pass

    except Exception as e:
        log_event("feedback_error", 
                 ip=client_ip,
                 error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send feedback: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)