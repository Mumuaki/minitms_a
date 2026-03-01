FROM nginx:1.25-alpine

# Удаляем дефолтный конфиг nginx
RUN rm /etc/nginx/conf.d/default.conf

# Копируем наш конфиг
COPY nginx.conf /etc/nginx/nginx.conf

# Проверяем синтаксис конфига при сборке образа
RUN nginx -t

EXPOSE 8000

CMD ["nginx", "-g", "daemon off;"]
