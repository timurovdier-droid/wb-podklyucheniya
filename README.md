# Бот заявок WB Taxi

Telegram-бот принимает заявки водителей на подключение и на брендирование машины. Анкета на узбекском. Готовая заявка уходит в группу администраторов, а если указана Google Таблица — ещё и строкой на лист `Ulanish` или `Brend`.

## Что умеет бот

- Выбор города и меню: подключение, бренд, контакты, офис.
- Подключение: номер кнопкой, предупреждение, 7 фото документов и 4 фото машины, госномер.
- Бренд: условия, ФИО, телефон, модель, год, цвет, госномер. Spark, Nexia 3 и машины 2015 года и старше не проходят.
- Офис: Мирзо-Улугбекский район, массив Ялангач, 100 (Эко бозор) и кнопка Яндекс.Карт. Если положить фото в `assets/office.jpg`, бот отправит его вместе с адресом.
- В группе у заявки кнопки «На связи», «Подключён», «Отклонён». Водитель получает сообщение, статус в таблице обновляется.

Фото документов в таблицу не записываются. Они остаются в альбоме группы.

Если в `.env` задан `GEMINI_API_KEY`, после заявки на **ulanish** бот отправит 7 документов в `gemini-3.8-flash` (модель — `GEMINI_MODEL`), подставит ФИО с документов и допишет блок **Gemini (hujjatlar)** в карточке для админов.

## Запуск

Нужен Python 3.11 или новее.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python -m bot.main
```

В `.env` обязательны `BOT_TOKEN` и `ADMIN_CHAT_ID`.

Токен берётся у [@BotFather](https://t.me/BotFather). Чтобы узнать id группы, добавьте бота в группу, напишите там `/chatid` и вставьте ответ в `ADMIN_CHAT_ID`. Обычно это число вида `-100...`.

Свои телефон, Telegram, канал и Instagram заполните в `SUPPORT_PHONE`, `OPERATOR_USERNAME`, `CHANNEL_URL`, `INSTAGRAM`. Пустые строки в карточке контактов не показываются.

Примеры фото, которые бот показывает перед каждым шагом, кладутся в `assets/examples/`:

- `passport.jpg`
- `license_front.jpg`
- `license_back.jpg`
- `tech_front.jpg`
- `tech_back.jpg`
- `selfie.jpg`
- `taxi_license.jpg`
- `car_front.jpg`, `car_rear.jpg`, `car_left.jpg`, `car_right.jpg` (или один `car.jpg`)

Голосовое предупреждение — `assets/warning.ogg`. Если файлов нет, бот просто пишет текст.

## Google Таблица

Пока `GOOGLE_SHEET_ID` пустой, бот работает только через Telegram.

1. В Google Cloud создайте сервисный аккаунт и скачайте JSON-ключ.
2. Положите ключ рядом с ботом как `credentials.json`. Этот файл не отправляйте никому.
3. Создайте таблицу и дайте email сервисного аккаунта право редактора.
4. Вставьте в `GOOGLE_SHEET_ID` ссылку на таблицу или её id.

Бот сам создаст листы `Ulanish` и `Brend` с заголовками, если первая строка пустая. Если заголовки уже есть, он заполнит знакомые колонки: дата, код, город, телефон, имя или ФИО, модель, год, цвет, госномер, статус, username, Telegram ID.

## Деплой на Vercel

1. Импортируйте репозиторий в [Vercel](https://vercel.com) (Framework Preset: **Other**).
2. В **Environment Variables** скопируйте все переменные из `.env.example` (включая `BOT_TOKEN`, `ADMIN_CHAT_ID`, `WORK_CHAT_ID`, `GEMINI_API_KEY` и т.д.).
3. После деплоя откройте `https://<ваш-проект>.vercel.app/api/health` — должен быть `{"status":"ok"}`.
4. Привяжите webhook (остановите локальный polling, иначе конфликт):

   ```powershell
   $env:BOT_TOKEN="..."
   $env:WEBHOOK_BASE_URL="https://<ваш-проект>.vercel.app"
   python scripts/set_webhook.py
   ```

5. Проверка: `https://api.telegram.org/bot<TOKEN>/getWebhookInfo`

**Важно:** на Vercel файловая SQLite в `data/` не сохраняется между вызовами. Для продакшена на Vercel нужна внешняя БД (позже) или запускайте бота локально/VPS через `python -m bot.main` (polling).

Локально по-прежнему: `python -m bot.main`.
