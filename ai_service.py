import json
import logging
import google.generativeai as genai
from config import GEMINI_API_KEY # config.py файлингиздан API калитни олади

logger = logging.getLogger(__name__)

# Gemini API ни созлаш
genai.configure(api_key=GEMINI_API_KEY)

# Моделни танлаш - энг тезкор ва арзон модел (Flash)
MODEL_NAME = 'gemini-1.5-flash'

# AI учун бошланғич кўрсатма (Ботингиз қандай ишлашини AI га тушунтирамиз)
# БУ ЕРДАГИ JSON ФОРМАТНИ ЎЗИНГИЗНИНГ process_ai_action ФУНКЦИЯНГИЗГА МОСЛАБ ОЛАСИЗ
SYSTEM_INSTRUCTION = """
Сиз ветеринария ва қишлоқ хўжалиги маҳсулотлари савдоси билан шуғулланувчи омбор ботининг ақлли ёрдамчисисиз.
Фойдаланувчининг матнини ёки расмини таҳлил қилиб, АЛБАТТА JSON форматда жавоб қайтаринг.
Жавобингиз фақат JSON бўлсин, бошқа ҳеч қандай сўз қўшманг.

Кутиладиган JSON форматлари:
- Сотув учун: {"action": "sell", "product": "дори номи", "quantity": 1, "customer": "исм", "type": "насия/нақд"}
- Кирим учун: {"action": "incoming", "product": "дори номи", "quantity": 10}
- Бошқа ҳолат: {"action": "unknown"}
"""

async def process_text_with_ai(text: str) -> dict:
    """Матнли хабарларни AI орқали таҳлил қилиш"""
    try:
        # Моделни чақириш
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=SYSTEM_INSTRUCTION
        )
        
        # AI дан жавоб олиш
        response = await model.generate_content_async(text)
        result_text = response.text.strip()
        
        # Markdown (```json) белгиларини тозалаш
        if result_text.startswith("```json"):
            result_text = result_text[7:-3].strip()
        elif result_text.startswith("```"):
            result_text = result_text[3:-3].strip()
            
        # JSON матнни Python луғатига (dict) ўгириш
        return json.loads(result_text)
        
    except Exception as e:
        logger.error(f"AI Матнни ўқишда хатолик: {e}")
        # Хатолик бўлса, бот қотиб қолмаслиги учун бўш амал қайтарамиз
        return {"action": "error", "message": str(e)}

async def process_image_with_ai(image_bytes: bytearray) -> dict:
    """Расмларни AI орқали таҳлил қилиш"""
    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=SYSTEM_INSTRUCTION
        )
        
        # Расмни тайёрлаш
        image_part = {
            "mime_type": "image/jpeg",
            "data": image_bytes
        }
        
        prompt = "Ушбу расмдаги маълумотларни (дори номи, сони, мижоз) ўқиб, омбор амалини аниқланг ва юқоридаги қоидага асосан JSON қайтаринг."
        
        # AI га расм ва сўровни юбориш
        response = await model.generate_content_async([prompt, image_part])
        result_text = response.text.strip()
        
        # Markdown (```json) белгиларини тозалаш
        if result_text.startswith("```json"):
            result_text = result_text[7:-3].strip()
        elif result_text.startswith("```"):
            result_text = result_text[3:-3].strip()
            
        return json.loads(result_text)
        
    except Exception as e:
        logger.error(f"AI Расмни ўқишда хатолик: {e}")
        return {"action": "error", "message": str(e)}
