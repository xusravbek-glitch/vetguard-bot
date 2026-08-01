import json
import logging
import google.generativeai as genai
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Барқарор ва тезкор модель номи
MODEL_NAME = 'gemini-2.5-flash'

SYSTEM_PROMPT = """
Сиз ветеринария аптекаси ва омбори учун жуда ақлли AI ERP ёрдамчисисиз.
Фойдаланувчи юборган ҳар қандай матн ёки накладной/чек расмидан амалларни аниқлаб, фақат ва фақат тоза JSON форматида қайтаринг. Ҳеч қандай қўшимча изоҳ ёки матн ёзманг.

МУҲИМ ҚОИДА: 
1. Агар расмда ёки матнда бир нечта товарлар (накладной) бўлса, уларни МАССИВ (JSON Array `[...]`) кўринишида қайтаринг. Агар битта товар бўлса оддий JSON объект қайтаринг.
2. Ҳар бир товар учун `action` асосан "sell" (сотиш) ёки "incoming" (кирим) бўлади.
3. Агар накладной бўлса, одатда бу "sell" ёки "incoming" амали ҳисобланади. Харидор кўрсатилмаган бўлса мижозни null қолдиринг.

JSON структураси (якка ҳолда):
{
  "action": "sell" | "incoming" | "pay_debt" | "add_product" | "add_customer" | "unknown",
  "product_name": "дори тўлиқ номи ва ҳажми",
  "customer_name": "мижоз исми ёки ҳудуд" ёки null,
  "quantity": сон (масалан: 1),
  "discount_percent": чегирма фоизи (сон) ёки 0,
  "discount_amount": чегирма суммаси (сон) ёки 0,
  "amount": қарз тўлови суммаси ёки null,
  "payment_type": "Нақд" | "Насия"
}
Ёки бир нечта товар учун мазкур объектлардан иборат массив `[ {...}, {...} ]` қайтаринг.
"""

async def process_text_with_ai(text: str):
    if not GEMINI_API_KEY:
        return {"action": "unknown"}

    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=SYSTEM_PROMPT
        )
        response = await model.generate_content_async(text)
        
        res_text = response.text.strip()
        logger.info(f"AI Raw Response: {res_text}")
        
        if "```json" in res_text:
            res_text = res_text.split("```json")[1].split("```")[0].strip()
        elif "```" in res_text:
            res_text = res_text.split("```")[1].split("```")[0].strip()
            
        return json.loads(res_text)
    except Exception as e:
        logger.error(f"Gemini Text Exception: {e}")
        return {"action": "unknown"}

async def process_image_with_ai(image_bytes: bytes, prompt_text: str = ""):
    if not GEMINI_API_KEY:
        return {"action": "unknown"}

    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=SYSTEM_PROMPT
        )
        
        image_part = {
            "mime_type": "image/jpeg",
            "data": image_bytes
        }
        
        user_input = [image_part, "Ушбу накладной ёки ҳужжат расмини диққат билан ўқиб, ундаги барча товарларни JSON массив ёки объект кўринишида батафсил қайтаринг."]
        if prompt_text:
            user_input.append(f"Қўшимча изоҳ: {prompt_text}")
        
        response = await model.generate_content_async(user_input)
        
        res_text = response.text.strip()
        logger.info(f"AI Image Raw Response: {res_text}")
        
        if "```json" in res_text:
            res_text = res_text.split("```json")[1].split("```")[0].strip()
        elif "```" in res_text:
            res_text = res_text.split("```")[1].split("```")[0].strip()
            
        return json.loads(res_text)
    except Exception as e:
        logger.error(f"Gemini Image Exception: {e}")
        return {"action": "unknown"}
