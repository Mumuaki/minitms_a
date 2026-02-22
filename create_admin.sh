#!/bin/bash
set -e
# Генерируем bcrypt-хэш для пароля admin123
HASH=$(docker exec minitms-backend python3 -c "import bcrypt; h=bcrypt.hashpw(b'admin123',bcrypt.gensalt(12)).decode(); print(h)")
echo "Hash generated: $HASH"

# Вставляем пользователя в БД через контейнер postgres
docker exec postgres psql -U admin -d minitms -c "
INSERT INTO users (email, username, password_hash, role, language, is_active, failed_login_attempts)
VALUES ('admin@minitms.local', 'Admin', '$HASH', 'administrator', 'ru', true, 0)
ON CONFLICT (email) DO NOTHING;
"
echo "INSERT_DONE"
docker exec postgres psql -U admin -d minitms -c "SELECT id, email, role FROM users;"
