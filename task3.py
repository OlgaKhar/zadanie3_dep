from langchain_community.chat_models import GigaChat
from langchain.prompts import PromptTemplate
import os
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List
import json
# from dotenv import load_dotenv  # dotenv больше не нужен

# Прямо указываем ключ
GIGACHAT_API_KEY = "OWZjN2M1ODMtMjM5MC00YTdmLWIyYzctZWE0Y2MzMjE1N2FjOmMyZWZjYzBmLTkyNGEtNDhlZC05MzlkLWEyZDc5ZjNjOWNmZQ=="

# Инициализация GigaChat
giga = GigaChat(credentials=GIGACHAT_API_KEY, verify_ssl_certs=False)

# Модель данных для обращения
class Appeal(BaseModel):
    date: str
    topic: str
    department: str

# Системный промпт для классификации обращений
template = """
Ты - система "Единое окно" для обработки обращений граждан. Твоя задача - точно определить, к какому департаменту относится обращение гражданина и выделить его тему.

Правила классификации:
1. Департамент транспорта:
   - Вопросы дорог, тротуаров, мостов
   - Проблемы с общественным транспортом
   - Вопросы парковок и стоянок
   - Проблемы с дорожным покрытием

2. Департамент культуры:
   - Вопросы работы музеев, театров, библиотек
   - Организация культурных мероприятий
   - Сохранение культурного наследия
   - Поддержка творческих инициатив

3. Департамент здравоохранения:
   - Вопросы работы больниц и поликлиник
   - Медицинское обслуживание
   - Санитарное состояние
   - Вакцинация и профилактика

4. Департамент образования:
   - Вопросы работы школ и детских садов
   - Образовательные программы
   - Учебные материалы
   - Внешкольное образование

5. Департамент экологии:
   - Вопросы уборки и благоустройства
   - Озеленение территорий
   - Экологические проблемы
   - Утилизация отходов

6. Департамент физической культуры и спорта:
   - Вопросы спортивных объектов
   - Организация спортивных мероприятий
   - Развитие массового спорта
   - Поддержка спортивных секций

Обращение гражданина: {appeal}

Проанализируй обращение и определи:
1. К какому департаменту оно относится
2. Тему обращения (кратко, в 2-3 слова)

Ответь ТОЛЬКО в формате JSON, без дополнительного текста:
{{
    "department": "название департамента",
    "topic": "тема обращения"
}}
"""

prompt = PromptTemplate(
    input_variables=["appeal"],
    template=template
)

def save_appeal_to_file(appeal: Appeal) -> None:
    """Сохраняет обращение в JSON файл"""
    filename = "requests.json"
    
    # Создаем список обращений
    appeals = []
    
    # Если файл существует, читаем существующие обращения
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                appeals = json.load(f)
        except json.JSONDecodeError:
            appeals = []
    
    # Добавляем новое обращение
    appeals.append(appeal.model_dump())
    
    # Записываем обновленный список обращений
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(appeals, f, ensure_ascii=False, indent=2)

def process_appeal(appeal_text: str) -> Optional[Appeal]:
    """Обработка обращения и определение соответствующего департамента"""
    try:
        formatted_prompt = prompt.format(appeal=appeal_text)
        response = giga.invoke(formatted_prompt)
        
        # Получаем текст ответа
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Очищаем текст от лишних символов и пробелов
        response_text = response_text.strip()
        
        # Находим начало и конец JSON в ответе
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            print(f"Получен некорректный ответ: {response_text}")
            raise ValueError("Не удалось найти JSON в ответе")
            
        json_str = response_text[start_idx:end_idx]
        
        try:
            # Парсим JSON
            response_data = json.loads(json_str)
            
            # Проверяем наличие необходимых полей
            if "department" not in response_data or "topic" not in response_data:
                raise ValueError("В ответе отсутствуют необходимые поля")
            
            # Создаем объект Appeal с текущей датой
            appeal_data = Appeal(
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                topic=response_data["topic"],
                department=response_data["department"]
            )
            
            # Сохраняем обращение в файл
            save_appeal_to_file(appeal_data)
            
            return appeal_data
            
        except json.JSONDecodeError as e:
            print(f"Ошибка при парсинге JSON: {e}")
            print(f"Полученная строка: {json_str}")
            return None
            
    except Exception as e:
        print(f"Ошибка при обработке обращения: {str(e)}")
        return None

def main():
    print("Добро пожаловать в систему 'Единое окно'!")
    print("Введите ваше обращение, и мы направим его в нужный департамент.")
    print("Для завершения работы введите 'выход'.")
    
    while True:
        print("\nВведите ваше обращение:")
        appeal = input().strip()
        
        if appeal.lower() == 'выход':
            print("Спасибо за использование системы 'Единое окно'. До свидания!")
            break
            
        if not appeal:
            print("Обращение не может быть пустым. Пожалуйста, введите текст обращения.")
            continue
            
        result = process_appeal(appeal)
        if result:
            print("\nРезультат обработки обращения:")
            print(result.model_dump_json(indent=2))
        else:
            print("Не удалось определить департамент. Пожалуйста, сформулируйте обращение более конкретно.")

if __name__ == "__main__":
    main() 