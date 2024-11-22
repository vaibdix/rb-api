import io
import os
import re
from datetime import datetime
from typing import Optional

# Third-party imports
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import (
    APIRouter,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image
from pydantic import BaseModel
import pdfplumber
import pytesseract

# Local imports
from configurations import collection
from database.models import RB
from database.schemas import all_tasks, individual_data

app = FastAPI(
    title="RB API",
    description="A simple RB API built with FastAPI and MongoDB",
    version="1.0.0"
)

# Enable CORS (cross-origin resource sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")
os.makedirs("documents", exist_ok=True)

class ExtractedData(BaseModel):
    permanent_account_number_card: Optional[str] = None
    name: Optional[str] = None
    date_of_birth: Optional[str] = None

def extract_text(file_bytes, content_type):
    try:
        if content_type.startswith('image/'):
            image = Image.open(io.BytesIO(file_bytes))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            return pytesseract.image_to_string(image)
        elif content_type == 'application/pdf':
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                return ' '.join(page.extract_text() or '' for page in pdf.pages)
        return None
    except Exception as e:
        print(f"Extraction error: {str(e)}")
        return None


def extract_data(text: str) -> ExtractedData:
    if not text:
        return ExtractedData()

    data = ExtractedData()
    text = text.upper()
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    pan_pattern = r'[A-Z]{5}[0-9]{4}[A-Z]'
    pan_matches = re.findall(pan_pattern, text)
    if pan_matches:
        data.permanent_account_number_card = pan_matches[0]

    for i, line in enumerate(lines):
        if ('NAME' in line or 'नाम' in line) and 'FATHER' not in line and 'FATHERS' not in line:
            name_parts = line.split('NAME')[-1].strip() if 'NAME' in line else line.split('नाम')[-1].strip()

            if name_parts and not any(x in name_parts for x in ['FATHER', 'DOB', 'DATE']):
                data.name = name_parts
                break
            elif i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and not any(x in next_line for x in ['FATHER', 'DOB', 'DATE', 'NAME']):
                    data.name = next_line
                    break

    dob_patterns = [
        r'\d{2}[/-]\d{2}[/-]\d{4}',
        r'\d{2}\s*[/-]\s*\d{2}\s*[/-]\s*\d{4}'
    ]

    for pattern in dob_patterns:
        dob_matches = re.findall(pattern, text)
        if dob_matches:
            data.date_of_birth = dob_matches[0].strip()
            break

    return data

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

router = APIRouter(prefix="/api/rbs", tags=["rbs"])


@app.post("/upload")
async def upload_file(docType: str = Form(...), file: UploadFile = File(...)):
    try:
        contents = await file.read()
        file_path = os.path.join("documents", file.filename)
        with open(file_path, "wb") as f:
            f.write(contents)

        extracted_text = extract_text(contents, file.content_type)

        if not extracted_text:
            return {
                "message": "Could not extract text from file",
                "extracted_text": None,
                "structured_data": None
            }

        structured_data = extract_data(extracted_text)

        return {
            "message": f"Successfully processed {docType}",
            "extracted_text": extracted_text,
            "structured_data": structured_data.dict()
        }
    except Exception as e:
        return {
            "message": f"Error processing file: {str(e)}",
            "extracted_text": None,
            "structured_data": None
        }


@router.get("/", response_description="List all rbs")
async def get_all_rbs():
    try:
        rbs = list(collection.find({"is_deleted": False}))
        if not rbs:
            return []
        return all_tasks(rbs)
    except Exception as e:
        print(f"Error in get_all_rbs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/", response_description="Create a new rb", status_code=status.HTTP_201_CREATED)
async def create_rb(rb: RB):
    try:
        rb_dict = rb.dict()
        insert_result = collection.insert_one(rb_dict)
        if insert_result.inserted_id:
            return individual_data({**rb_dict, "_id": insert_result.inserted_id})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create rb"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/{rb_id}", response_description="Get a single rb")
async def get_rb(rb_id: str):
    try:
        rb = collection.find_one({"_id": ObjectId(rb_id), "is_deleted": False})
        if rb:
            return individual_data(rb)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RB with ID {rb_id} not found"
        )
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid rb ID format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.put("/{rb_id}", response_description="Update a rb")
async def update_rb(rb_id: str, rb: RB):
    try:
        update_result = collection.update_one(
            {"_id": ObjectId(rb_id), "is_deleted": False},
            {"$set": {
                "panid": rb.panid,
                "name": rb.name,
                "dob": rb.dob,
                "is_completed": rb.is_completed,
                "updated_at": int(datetime.utcnow().timestamp())
            }}
        )

        if update_result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"RB with ID {rb_id} not found"
            )

        update_rb = collection.find_one({"_id": ObjectId(rb_id)})
        return individual_data(update_rb)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid rb ID format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )




@router.delete("/{rb_id}", response_description="Delete a rb", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rb(rb_id: str):
    try:
        delete_result = collection.delete_one({"_id": ObjectId(rb_id)})

        if delete_result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"RB with ID {rb_id} not found"
            )
        return None
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid rb ID format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/test", response_description="Add test rb")
async def add_test_rb():
    try:
        test_rb = {
            "panid": "TEST123",
            "name": "Test Name",
            "dob": "2000-01-01",
            "is_completed": False,
            "is_deleted": False,
            "updated_at": int(datetime.utcnow().timestamp()),
            "creation": int(datetime.utcnow().timestamp())
        }
        insert_result = collection.insert_one(test_rb)
        if insert_result.inserted_id:
            return individual_data({**test_rb, "_id": insert_result.inserted_id})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create test rb"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)