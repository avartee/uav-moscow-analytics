import os
import json
import feedparser
import google.generativeai as genai
from datetime import datetime, timedelta

# Настройка API ключа ИИ (берется из секретов GitHub)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

def fetch_morning_news():
    """Собирает новости по RSS-лентам за последние 24 часа"""
    news_texts = []
    # Реальные RSS-ленты для парсинга (можно добавлять свои)
    rss_urls = [
        "https://lenta.ru/rss/news",
        "https://rssexport.rbc.ru/rbcnews/news/30/full.rss"
    ]
    
    keywords = ["бпла", "беспилотник", "атака", "взрыв", "пво", "московск", "дрон"]
    
    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]: # Берем свежие
                title_lower = entry.title.lower()
                if any(word in title_lower for word in keywords):
                    news_texts.append(f"{entry.title}: {entry.get('description', '')}")
        except Exception as e:
            print(f"Ошибка парсинга {url}: {e}")
                
    return "\n".join(news_texts)

def analyze_with_ai(news_text, current_data):
    """Отправляет новости и текущую базу в Gemini для анализа"""
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    prompt = f"""
    Ты военный аналитик. Твоя задача - обновить JSON базу данных на основе свежих новостей.
    
    Текущая база данных (JSON):
    {json.dumps(current_data, ensure_ascii=False)}
    
    Сводка новостей за 24 часа:
    {news_text if news_text else "Новых инцидентов не зафиксировано."}
    
    Инструкция:
    1. Если в новостях ЕСТЬ информация о новых ударах или падениях БПЛА в Москве/МО, добавь их в массив 'pastIncidents'. Координаты (coords) укажи примерные [широта, долгота].
    2. Проанализируй вектор. Если логика ударов сместилась, обнови массив 'forecastTargets' (ТОП-30). Если новостей об атаках нет - оставь базу без изменений.
    3. Верни ТОЛЬКО валидный JSON-код. Никаких вступлений, маркдауна или тегов ```json.
    
    Формат ответа:
    {{ "pastIncidents": [...], "forecastTargets": [...] }}
    """
    
    response = model.generate_content(prompt)
    clean_json = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_json)

if __name__ == "__main__":
    print(f"[{datetime.now()}] Начинаю утренний сбор разведданных...")
    
    try:
        # 1. Читаем текущую базу
        with open('data.json', 'r', encoding='utf-8') as f:
            current_data = json.load(f)
            
        # 2. Собираем новости
        news = fetch_morning_news()
        
        # 3. Отправляем в ИИ (даже если новостей мало, ИИ может переоценить риски)
        print("Передаю данные ИИ-аналитику...")
        updated_data = analyze_with_ai(news, current_data)
        
        # 4. Сохраняем обновленные данные
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=4)
        print("Успех: База data.json обновлена!")
        
    except Exception as e:
        print(f"Ошибка в процессе обновления: {e}")
