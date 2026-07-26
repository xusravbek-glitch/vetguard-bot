import json
import logging
import google.generativeai as genai
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Модель номи 3.5 Flash-Lite га янгиланди
MODEL_NAME = 'gemini-3.5-flash-lite'

SYSTEM_PROMPT = """
Сиз ветеринария аптекаси ва омбори учун жуда ақлли AI ERP ёрдамчисисиз.
Фойдаланувчи юборган ҳар қандай матн ёки расмдан (масалан: "Сотув Клозатрем 250мл 1дона Шахбоз Каршига насияга" ёки "Фосбевит 10мл 1 дона Шахбозга") амални аниқлаб, фақат ва фақат тоза JSON форматида қайтаринг. Ҳеч қандай қўшимча изоҳ ёки матн ёзманг.

МУҲИМ ҚОИДА: 
1. Агар матн "Сотув" сўзи билан бошланса ёки унда дори номи, сони ва мижоз/ҳудуд кўрсатилган бўлса, `action` ҳеч қачон "unknown" бўлмасин, у **доимо "sell"** бўлсин.
2. Агар матнда "насия", "қарзга" деган сўзлар бўлса, `payment_type` ни **"Насия"** қилинг, қолган ҳолларда **"Нақд"** қилинг.

Операция турлари (action):
1. "sell" - Сотиш (Чегирма бўлиши мумкин)
2. "incoming" - Омборга кирим/келди
3. "pay_debt" - Қарзни тўлаш
4. "add_product" - Янги дори қўшиш
5. "add_customer" - Янги мижоз қўшиш
6. "unknown" - Фақат тушунарсиз ва маъносиз сўзлар бўлсагина.

JSON структураси фақат шу кўринишда бўлсин:
{
  "action": "sell" | "incoming" | "pay_debt" | "add_product" | "add_customer" | "unknown",
  "product_name": "дори тўлиқ номи ва ҳажми" ёки null,
  "customer_name": "мижоз исми ёки ҳудуд" ёки null,
  "quantity": сон (масалан: 1) ёки null,
  "discount_percent": чегирма фоизи (сон) ёки 0,
  "discount_amount": чегирма суммаси (сон) ёки 0,
  "amount": қарз тўлови ёки умумий сумма (сон) ёки null,
  "payment_type": "Нақд" | "Насия"
}
"""

async def process_text_with_ai(text: str) -> dict:
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

async def process_image_with_ai(image_bytes: bytes, prompt_text: str = "") -> dict:
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
        
        user_input = [image_part, "Ушбу ҳужжат, чек ёки қўлёзма суратини таҳлил қилиб, белгиланган форматда JSON қайтаринг."]
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
