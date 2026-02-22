# Multi-stage build для Frontend (React + Vite)

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Копирование package.json и package-lock.json
COPY package*.json ./

# Установка зависимостей
RUN npm ci

# Копирование исходного кода
COPY . .

# Сборка production версии
RUN npm run build

# Stage 2: Production
FROM nginx:alpine

# Копирование собранных файлов из builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Копирование конфигурации nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose порт
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
