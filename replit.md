# SAZ LogicTranway - Логистика транспортных путей

## Обзор проекта

Веб-приложение для логистики транспортных путей с интеграцией Yandex Maps. Позволяет управлять заявками на перевозку грузов, назначать транспортные средства и отслеживать маршруты.

## Технологии

### Backend
- **Python 3.11** с Flask
- **SQLite** база данных через Flask-SQLAlchemy
- **Flask-JWT-Extended** для аутентификации
- **Flask-CORS** для CORS
- **pdfkit** для генерации PDF (ТТН)
- **openpyxl** для экспорта в Excel

### Frontend
- HTML/CSS/JavaScript
- Yandex Maps API для отображения маршрутов
- Bootstrap 4 для стилизации

## Структура проекта

```
├── backend/
│   ├── app.py          # Основной Flask-сервер и API
│   ├── database.db     # SQLite база данных
│   ├── init_db.py      # Инициализация БД
│   └── reset_db.py     # Сброс БД
├── src/
│   ├── index.html      # Главная страница (форма груза)
│   ├── admin.html      # Панель диспетчера
│   ├── login.html      # Страница входа
│   ├── confirm.html    # Подтверждение назначения
│   ├── script.js       # Основная логика фронтенда
│   ├── admin.js        # Логика админ-панели
│   ├── confirm.js      # Логика подтверждения
│   └── style.css       # Стили
├── package.json        # Node.js зависимости
└── requirements.txt    # Python зависимости
```

## Запуск проекта

Приложение запускается через workflow "Start application":
```bash
cd backend && python app.py
```

Flask-сервер обслуживает и API, и статические файлы на порту 5000.

## API Endpoints

### Аутентификация
- `POST /login` - Вход в систему

### Грузы (черновик)
- `GET /draft_cargos` - Получить список черновых грузов
- `POST /draft_cargos` - Добавить груз в черновик
- `DELETE /draft_cargos/<id>` - Удалить груз из черновика
- `DELETE /draft_cargos/clear` - Очистить черновик

### Заявки
- `GET /orders` - Получить все заявки
- `GET /orders/<id>` - Получить заявку по ID
- `POST /orders` - Создать новую заявку
- `POST /orders/<id>/assign` - Назначить машину на заявку
- `POST /orders/<id>/complete` - Завершить заявку

### Транспорт
- `GET /vehicles` - Получить список машин
- `POST /vehicles` - Добавить машину
- `PUT /vehicles/<id>` - Обновить статус машины

### Подбор транспорта
- `POST /match` - Подобрать подходящий транспорт
- `GET /suggest_vehicle/<order_id>` - Предложить машину для заявки

### Экспорт
- `GET /export_orders` - Экспорт заявок в Excel
- `GET /ttn/<order_id>` - Сгенерировать ТТН в PDF

## Учетные записи по умолчанию

- **Пользователь**: user / sazwork205
- **Администратор**: admin / sazadmin2025

## Последние изменения

- 02.12.2025: Настроен проект для работы в Replit (ветка dev_3)
  - Flask обслуживает и API и статические файлы на порту 5000
  - Настроены относительные API URLs во фронтенде
