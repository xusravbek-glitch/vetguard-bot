import json
import logging
import io
from PIL import Image
from google import genai
from google.genai import types
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

# Янги кутубхона учун мижозни (client) асосий sozlash
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# Энг барқарор ва тезкор модел номи
MODEL_NAME = 'gemini-2.5-flash'

SYSTEM_PROMPT = """
Сиз ветеринария аптекаси ва омбори учун жуда ақлли AI ERP ёрдамчисисиз.
Фойдаланувчи юборган ҳар қандай матн ёки расмдан амални аниқлаб, фақат ва фақат тоза JSON форматида қайтаринг. 

МУҲИМ ҚОИДАЛАР: 
1. Агар расмда накладной бўлса (бир нечта товар), албатта JSON массив (Array) қайтаринг: [ {...}, {...} ]
2. Агар матнда фақат битта товар бўлса ҳам, уни албатта массив ичида қайтаринг: [ {...} ]
3. Ҳеч қандай қўшимча изоҳ ёки матн ёзманг. Фақат JSON!

JSON структураси (ҳар бир товар учун):
{
  "action": "sell" | "incoming" | "pay_debt" | "add_product" | "add_customer" | "unknown",
  "product_name": "дори тўлиқ номи ва ҳажми" ёки null,
  "customer_name": "мижоз исми ёки ҳудуд" ёки null,
  "quantity": сон (масалан: 1) ёки 0,
  "discount_percent": чегирма фоизи (сон) ёки 0,
  "discount_amount": чегирма суммаси (сон) ёки 0,
  "amount": қарз тўлови ёки умумий сумма (сон) ёки null,
  "payment_type": "Нақд" | "Насия"
}
"""

def extract_json_data(text: str) -> list:
    """ AI жавобидан JSON ни қирқиб олиш ва доимо list қайтариш """
    try:
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        start = text.find('[')
        end = text.rfind(']') + 1
        
        if start == -1 or end == 0:
            start = text.find('{')
            end = text.rfind('}') + 1
            
        if start != -1 and end != 0:
            text = text[start:end]
            
        data = json.loads(text)
        
        if isinstance(data, dict):
            return [data]
        return data if isinstance(data, list) else [{"action": "unknown"}]
        
    except Exception as e:
        logger.error(f"JSON Parsing Error: {e}\nRaw Response: {text}")
        return [{"action": "unknown"}]

async def process_text_with_ai(text: str) -> list:
    if not client:
        return [{"action": "unknown"}]

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=text,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT
            )
        )
        return extract_json_data(response.text)
    except Exception as e:
        logger.error(f"Gemini Text Exception: {e}")
        return [{"action": "unknown"}]

async def process_image_with_ai(image_bytes: bytes, prompt_text: str = "") -> list:
    if not client:
        return [{"action": "unknown"}]

    try:
        image = Image.open(io.BytesIO(image_bytes))
        
        user_input = [image, "Ушбу ҳужжат ёки накладной суратини таҳлил қилиб, барча товарлар учун белгиланган форматда JSON массив қайтаринг."]
        if prompt_text:
            user_input.append(f"Қўшимча изоҳ: {prompt_text}")
        
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_input,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT
            )
        )
        return extract_json_data(response.text)
    except Exception as e:
        logger.error(f"Gemini Image Exception: {e}")
        return [{"action": "unknown"}]
