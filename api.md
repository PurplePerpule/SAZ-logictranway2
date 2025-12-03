Здравствуйте,

Спасибо за вашу покупку. Ниже вы найдете учетные данные доступа к OpenAI API с прямым доступом к OpenAI.

1. Ваши учетные данные OpenAI API

Вы получили выделенный проект OpenAI с управлением бюджетом.

API Base URL: https://api.openai.com/v1
Ваш API ключ: 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
Выделенный бюджет: $1.00 USD
2. Быстрый старт: Пример на Python

Вот простой пример на Python с использованием официальной библиотеки openai:

from openai import OpenAI

client = OpenAI(
    api_key="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"
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Привет мир"}]
)
print(response.choices[0].message.content)
3. Пример cURL

curl -X POST 'https://api.openai.com/v1/chat/completions' \
-H 'Content-Type: application/json' \
-H 'Authorization: Bearer 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' \
-d '{
  "model": "gpt-4o-mini",
  "messages": [
        {"role": "user", "content": "Скажи тест."}
    ]
}'
4. Управление бюджетом и мониторинг

Мониторинг бюджета: Использование вашего проекта автоматически контролируется каждые 5 минут.
Лимит бюджета: Когда ваше использование достигнет $1.00 USD, все лимиты запросов будут автоматически установлены на 0, что предотвратит дальнейшее использование API.
5. Важная информация

Это прямой ключ OpenAI API (не через прокси/шлюз).
Бюджет строго контролируется и применяется автоматически.
После исчерпания бюджета проект будет автоматически заблокирован.
Все стандартные модели OpenAI доступны для использования с этим ключом.
6. Поддержка и помощь

Мы здесь, чтобы помочь вам добиться успеха. Пожалуйста, свяжитесь с нами, если:

Вам нужна помощь в интеграции API ключа с вашим приложением.
Вы столкнулись с техническими проблемами или у вас есть вопросы.
Вам нужны разъяснения по управлению бюджетом.
7. Бонус за отзыв

Мы ценим ваши отзывы. В знак благодарности вы автоматически получите купон на скидку 5% на следующую покупку после оставления положительного отзыва.

С уважением, Команда поддержки
