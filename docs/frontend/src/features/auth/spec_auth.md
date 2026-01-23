# Feature Specification: Authentication & Authorization (Auth)

| Атрибут | Значение |
| :--- | :--- |
| **Версия** | 1.0 |
| **Статус** | Draft |
| **Модуль** | Frontend / Features / Auth |
| **Связанные требования** | FR-AUTH-001 — FR-AUTH-005, FR-LOC-001 |

## 1. Обзор
Модуль **auth** отвечает за управление доступом пользователей к системе MiniTMS. Он обеспечивает процессы входа в систему, сохранения сессии, автоматического обновления токенов доступа (Refresh Token flow) и разграничения прав доступа к интерфейсам на основе ролей (RBAC).

## 2. Функциональные требования

### 2.1 Основные функции
* **Аутентификация:** Вход в систему по логину и паролю.
* **Управление сессией:** Поддержка функции "Запомнить меня" (долгоживущий токен на 30 дней).
* **Безопасность:** Обработка блокировки аккаунта после 5 неудачных попыток на 15 минут.
* **Локализация:** Выбор языка интерфейса (RU, EN, SK, PL) на экране входа до авторизации.
* **Выход:** Завершение сессии и очистка локального хранилища.

### 2.2 Ролевая модель
Система поддерживает 4 роли пользователей с разным уровнем доступа:
1. **Administrator:** Полный доступ, управление пользователями.
2. **Director:** Полный доступ к бизнесу, нет доступа к администрированию пользователей.
3. **Dispatcher:** Операционная работа: грузы, флот, email. Ограничен в финансах.
4. **Observer:** Только просмотр отчетов и статусов.

## 3. Архитектура UI компонентов

### 3.1 Страница входа (LoginPage)
Публичный маршрут (`/login`).
* **Layout:** Центрированная карточка на нейтральном фоне.
* **Элементы:**
    * `Logo`: Логотип MiniTMS.
    * `Language Switcher`: Dropdown для выбора языка (RU/EN/SK/PL).
    * `LoginForm`: Компонент формы.

### 3.2 Форма входа (LoginForm)
* **Поля ввода:**
    * `username` (text): Обязательное поле.
    * `password` (password): Обязательное поле, иконка "глаз" для просмотра введенного пароля.
* **Контролы:**
    * `rememberMe` (checkbox): "Запомнить меня". При активации срок жизни refresh-токена увеличивается до 30 дней.
    * `Submit Button`: "Войти" (Блокируется при состоянии isLoading).
* **Обработка ошибок:**
    * Валидация полей (клиентская).
    * Вывод сообщения о блокировке ("Аккаунт заблокирован. Попробуйте через 15 минут").
    * Вывод сообщения о неверных учетных данных.

### 3.3 Защита маршрутов (ProtectedRoute)
Компонент высшего порядка (HOC) или Layout-wrapper.
* **Логика:** Проверяет наличие флага `isAuthenticated` в стейте.
* **Действие:**
    * Если `true` -> рендерит дочерние компоненты (`Outlet`).
    * Если `false` -> перенаправляет на `/login` с сохранением `returnUrl`.

### 3.4 Контроль ролей (RoleGuard / PermissionGate)
Компонент для условного рендеринга частей интерфейса.
* **Props:** `allowedRoles: UserRole[]`.
* **Логика:** Сравнивает роль текущего пользователя (`user.role`) с массивом `allowedRoles`.
* **Пример использования:** Скрытие кнопки "Настройки" для ролей Dispatcher и Observer.

## 4. State Management (Redux Slice)
Используется `authSlice` для хранения глобального состояния аутентификации.

```typescript
// Types
type UserRole = 'Administrator' | 'Director' | 'Dispatcher' | 'Observer';

interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  language: 'ru' | 'en' | 'sk' | 'pl';
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// Initial State
const initialState: AuthState = {
  user: null,
  accessToken: null, // Хранится в памяти (Redux)
  isAuthenticated: false,
  isLoading: false,
  error: null,
};
```

### 4.1 Actions (Thunks)
* `login(credentials)`:
    * Отправка POST запроса.
    * При успехе: сохранение `accessToken` в стейт, декодирование данных пользователя, редирект на Dashboard.
    * При ошибке: запись кода ошибки в стейт.
* `logout()`:
    * Отправка запроса на инвалидацию сессии.
    * Полная очистка стейта и LocalStorage.
* `checkAuth()`:
    * Вызывается при инициализации приложения. Пытается обновить токен (refresh) если пользователь закрывал вкладку.

## 5. Интеграция с API
Все запросы используют `axios` instance.

| Метод | URL | Описание | Заголовки |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login` | Вход в систему | - |
| `POST` | `/api/v1/auth/refresh` | Обновление Access Token | `Cookie: refreshToken` |
| `POST` | `/api/v1/auth/logout` | Выход из системы | `Authorization: Bearer {token}` |
| `GET` | `/api/v1/auth/me` | Получение профиля пользователя | `Authorization: Bearer {token}` |

### 5.1 Axios Interceptors
* **Request Interceptor:** Автоматически добавляет заголовок `Authorization: Bearer <token>` ко всем запросам, если токен есть в стейте.
* **Response Interceptor:** Перехватывает ошибку 401 Unauthorized.
    * При получении 401 пытается выполнить запрос к `/refresh`.
    * Если refresh успешен -> повторяет исходный запрос с новым токеном.
    * Если refresh провалился -> вызывает `logout()` и редиректит на логин.

## 6. Безопасность и Валидация
### 6.1 Хранение токенов
* **Access Token:** Хранится только в памяти приложения (Redux State) для защиты от XSS.
* **Refresh Token:** Хранится в `httpOnly secure Cookie` для защиты от XSS и доступа из JS.

### 6.2 Матрица доступа (Frontend Enforcement)
Реализация логики скрытия элементов UI на основе требований.

| Раздел UI / Функция | Administrator | Director | Dispatcher | Observer |
| :--- | :---: | :---: | :---: | :---: |
| Settings (Настройки) | ✅ | ✅ | ❌ | ❌ |
| Fleet (Редактирование) | ✅ | ✅ | ✅ | ❌ |
| Finance (Планы) | ✅ | ✅ | ❌ | ❌ |
| Email Sending | ✅ | ✅ | ✅ | ❌ |
| Reports (Экспорт) | ✅ | ✅ | ✅ | ❌ |