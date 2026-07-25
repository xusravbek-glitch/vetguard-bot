import requests
import json
import base64
import logging
from config import DEEPSEEK_API_KEY

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
Сиз ветеринария аптекаси ва омбори учун AI ERP ёрдамчисисиз.
Фойдаланувчи юборган эркин матн ёки расмдан (юклама, чек, қўлёзма) амални аниқлаб, фақат ва фақат JSON форматида қайтаринг.

Операция турлари (action):
1. "sell" - Сотиш (Скидка/чегирма бўлиши мумкин)
2. "incoming" - Омборга кирим/келди
3. "pay_debt" - Қарзни тўлаш
4. "add_product" - Янги дори қўшиш
5. "add_customer" - Янги мижоз қўшиш
6. "unknown" - Тушунарсиз бўлса.

JSON структураси:
{
  "action": "sell" | "incoming" | "pay_debt" | "add_product" | "add_customer" | "unknown",
  "product_name": "дори номи" ёки null,
  "customer_name": "мижоз исми" ёки null,
  "quantity": сон ёки null,
  "discount_percent": чегирма фоизи (сон, масалан 10) ёки 0,
  "discount_amount": чегирма суммаси (сон, масалан 50000) ёки 0,
  "amount": қарз тўлови ёки умумий сумма (сон) ёки null,
  "payment_type": "Нақд" | "Насия" (стандарт: "Нақд")
}
"""

async def process_text_with_ai(text: str) -> dict:
    if not DEEPSEEK_API_KEY:
        return {"action": "unknown"}

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        "response_format": {"type": "json_object"}
    }

    try:
        response = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            res_content = response.json()["choices"][0]["message"]["content"]
            return json.loads(res_content)
        else:
            logger.error(f"AI Text API Error: {response.status_code} - {response.text}")
            return {"action": "unknown"}
    except Exception as e:
        logger.error(f"AI Text Exception: {e}")
        return {"action": "unknown"}

async def process_image_with_ai(image_bytes: bytearray) -> dict:
    if not DEEPSEEK_API_KEY:
        return {"action": "unknown"}

    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user", 
                "content": f"Ушбу хужжат/чек ёки қўлёзма суратини аниқланг ва JSON қайтаринг: data:image/jpeg;base64,{base64_image}"
            }
        ]
    }

    try:
        response = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            res_content = response.json()["choices"][0]["message"]["content"]
            start_idx = res_content.find('{')
            end_idx = res_content.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                return json.loads(res_content[start_idx:end_idx])
            return json.loads(res_content)
        else:
            logger.error(f"AI Image API Error: {response.status_code} - {response.text}")
            return {"action": "unknown"}
    except Exception as e:
        logger.error(f"AI Image Exception: {e}")
        return {"action": "unknown"}
