from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
# ... (imports)


from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import pydantic
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import shutil
import os
import uuid
from dotenv import load_dotenv
from analyzer.extractor import extract_zip_and_find_logs
from analyzer.parser import parse_logs
from analyzer.parser import parse_logs
from analyzer.llm import analyze_with_llm, test_api_connection
from analyzer.report_generator import generate_pdf_report

load_dotenv()

app = FastAPI()

# Mount static files for the frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# Directories
UPLOAD_DIR = "uploads"
REPORT_DIR = "reports"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

@app.get("/config")
async def get_config():
    """Returns public configuration status (not secret keys)"""
    return {
        "has_api_key": bool(os.getenv("OPENAI_API_KEY")),
        "has_cambrian_token": bool(os.getenv("CAMBRIAN_TOKEN"))
    }

class ConnectionTestRequest(pydantic.BaseModel):
    provider: str
    api_key: str

@app.post("/test_connection")
async def test_connection_endpoint(request: ConnectionTestRequest):
    success, message = await test_api_connection(request.provider, request.api_key)
    return {"success": success, "message": message}

@app.post("/analyze")
async def analyze_logs(
    file: UploadFile = File(...), 
    openai_api_key: str = Form(None), 
    cambrian_token: str = Form(None),
    model: str = "gpt-4o"
):
    # Use provided key or fallback to env var for OpenAI
    final_openai_key = openai_api_key or os.getenv("OPENAI_API_KEY")
    final_cambrian_token = cambrian_token or os.getenv("CAMBRIAN_TOKEN")
    
    # Analyze logic handles which key to use based on model
    
    session_id = str(uuid.uuid4())
    session_upload_dir = os.path.join(UPLOAD_DIR, session_id)
    os.makedirs(session_upload_dir, exist_ok=True)
    
    file_path = os.path.join(session_upload_dir, file.filename)
    
    # Save the uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Check if it is a zip file
        if file.filename.endswith(".zip"):
            # 1. Extract
            log_files = extract_zip_and_find_logs(file_path, session_upload_dir)
        else:
            # Treats single text file as a bugreport/log
            log_files = {
                "bugreport": file_path,
                "anr_files": [],
                "other_logs": []
            }
        
        # 2. Parse
        parsed_data = parse_logs(log_files)
        
        # 3. LLM Analyze
        analysis_result = await analyze_with_llm(
            parsed_data, 
            openai_api_key=final_openai_key, 
            cambrian_token=final_cambrian_token, 
            model=model
        )
        
        # 4. Generate Report
        report_paths = generate_pdf_report(analysis_result, session_id, REPORT_DIR)
        
        return JSONResponse(content={
            "session_id": session_id,
            "reports": report_paths,
            "status": "success"
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        # Cleanup upload dir to save space (optional, maybe keep for debug)
        # shutil.rmtree(session_upload_dir)
        pass

@app.get("/reports/{filename}")
async def get_report(filename: str):
    file_path = os.path.join(REPORT_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return HTTPException(status_code=404, detail="File not found")
