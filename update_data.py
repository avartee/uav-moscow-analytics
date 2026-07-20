try:
    new_data = json.loads(raw_text)
    
    # Обрабатываем маркеры новизны
    for incident in new_data.get('pastIncidents', []):
        if incident.pop('is_new', False): # Если ИИ пометил как новое, ставим таймстамп
            incident['added_at'] = current_time
            
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    print("Данные успешно обновлены ИИ.")
except Exception as e:
    print(f"Ошибка парсинга JSON от ИИ: {e}")
    exit(1)
