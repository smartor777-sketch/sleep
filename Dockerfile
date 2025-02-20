# Используем официальный образ Python
FROM python:3.13-rc

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем все файлы проекта в контейнер
COPY . .

# Устанавливаем зависимости из requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Указываем переменную окружения для работы с config.yaml
ENV CONFIG_PATH="/app/config.yaml"

# Открываем порт, который будет использовать бот (если нужно)
EXPOSE 8080

# Запускаем бота через точку входа __main__.py
CMD ["python", "main.py"]
