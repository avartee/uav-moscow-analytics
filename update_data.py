import os
import json
import feedparser
import datetime
import google.generativeai as genai

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in environment.")
    exit(1)

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-pro')

try:
    with open('data.json', 'r', encoding='utf-8') as f:
        current_data = json.load(f)
except FileNotFoundError:
    print("Error: data.json not found.")
    exit(1)

feed = feedparser.parse('https://lenta.ru/rss/news')
news_text = "Свежие новости:\n"
found_news = False

for entry in feed.entries[:40]:
    title_desc = (entry.title + " " + entry.description).lower()
    if any(word in title_desc for word in ['бпла', 'беспилотник', 'дрон', 'пво', 'взрыв', 'моск']):
        news_text += f"- {entry.title}: {entry.description}\n"
        found_news = True

if not found_news:
    print("No new UAV attack news found.")
    exit(0)

current_time = datetime.datetime.utcnow().isoformat() + "Z"
prompt = f"""
Ты — аналитик Генштаба РФ [Inference]. 
База данных: {json.dumps(current_data, ensure_ascii=False)}
Свежие новости: {news_text}

Инструкция:
1. Если в новостях есть НОВЫЕ удары БПЛА по Московскому региону, добавь их в "pastIncidents". 
2. ВАЖНО: Для каждого нового удара обязательно добавь поле "is_new": true и поле "details": "Укажи населенный пункт, атакованный объект и характер повреждений".
3. Обнови ТОП-30 в "forecastTargets" на основе новых данных.
4. Верни СТРОГО валидный JSON (ключи pastIncidents, forecastTargets). Без markdown разметки и текста, только чистый JSON.
"""

response = model.generate_content(prompt)
raw_text = response.text.replace('```json', '').replace('```', '').strip()

try:
    new_data = json.loads(raw_text)
    
    # Process "is_new" markers
    for incident in new_data.get('pastIncidents', []):
        if incident.pop('is_new', False):
            incident['added_at'] = current_time
            
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    print("Data updated successfully.")
except Exception as e:
    print(f"Failed to parse JSON: {e}")
    exit(1)
