import os, json, feedparser, datetime, google.generativeai as genai

api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-pro')

# Список слов для жесткой фильтрации новостей
KEYWORDS = ['бпла', 'дрон', 'ракета', 'пво', 'удар', 'беспилотник']

def is_relevant(text):
    return any(word in text.lower() for word in KEYWORDS)

try:
    with open('data.json', 'r', encoding='utf-8') as f:
        current_data = json.load(f)
except:
    current_data = {"pastIncidents": [], "forecastTargets": []}

feed = feedparser.parse('https://lenta.ru/rss/news')
news_text = "Свежие новости:\n"
found_count = 0

for entry in feed.entries[:40]:
    title_desc = (entry.title + " " + entry.description).lower()
    if is_relevant(title_desc):
        news_text += f"- {entry.title}: {entry.description}\n"
        found_count += 1

if found_count == 0:
    exit(0)

current_time = datetime.datetime.utcnow().isoformat() + "Z"

prompt = f"""
Ты — аналитик Генштаба РФ. 
База: {json.dumps(current_data, ensure_ascii=False)}
Новости: {news_text}

Инструкция:
1. Выбери ТОЛЬКО свежие атаки БПЛА/ракет из новостей.
2. Добавь их в pastIncidents. Укажи: name, coords (примерные), details (объект и повреждения).
3. Добавь поле "is_new": true для новых событий.
4. Обнови forecastTargets.
5. Верни ТОЛЬКО валидный JSON.
"""

response = model.generate_content(prompt)
raw_text = response.text.replace('
```json','').replace('```','').strip()

new_data = json.loads(raw_text)
for incident in new_data.get('pastIncidents', []):
    if incident.pop('is_new', False): 
        incident['added_at'] = current_time
        
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(new_data, f, ensure_ascii=False, indent=2)
