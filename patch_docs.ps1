function Replace-FileContent {
    param ($Path, $Pattern, $Replacement)
    if (Test-Path $Path) {
        $content = Get-Content -Path $Path -Raw
        $content = [System.Text.RegularExpressions.Regex]::Replace($content, $Pattern, $Replacement)
        Set-Content -Path $Path -Value $content -Encoding UTF8
    }
}

# 1. spec_entities.md (уже КГ, но можно добавить пометку, если надо. Оставим как есть)
# 2. spec_dto.md -> Заменить 'т' на 'кг'
Replace-FileContent "d:\MiniTMS\docs\backend\src\application\dto\spec_dto.md" "\(т\)" "(кг)"

# 3. CHECKLIST.md -> PostgreSQL 14+ на 15+
Replace-FileContent "d:\MiniTMS\docs\CHECKLIST.md" "PostgreSQL 14\+" "PostgreSQL 15+"

# 4. spec_messaging.md -> RabbitMQ на Celery + Redis
Replace-FileContent "d:\MiniTMS\docs\backend\messaging\spec_messaging.md" "RabbitMQ" "Celery/Redis"

# 5. spec_gps.md -> Wialon/Navixy на GPS Guard
Replace-FileContent "d:\MiniTMS\docs\backend\src\infrastructure\external_services\gps\spec_gps.md" "(?i)(Wialon|Navixy)" "GPS Guard"

# 6. spec_telegram.md -> Пометить как отложен
$tgPath = "d:\MiniTMS\docs\backend\src\infrastructure\external_services\telegram\spec_telegram.md"
if (Test-Path $tgPath) {
    Set-Content -Path $tgPath -Value "# Спецификация интеграции Telegram`n`n**СТАТУС: ОТЛОЖЕНО** (см. PROJECT-CONFIG.md).`nВременно не реализуется." -Encoding UTF8
} else {
    New-Item -ItemType File -Path $tgPath -Force
    Set-Content -Path $tgPath -Value "# Спецификация интеграции Telegram`n`n**СТАТУС: ОТЛОЖЕНО** (см. PROJECT-CONFIG.md).`nВременно не реализуется." -Encoding UTF8
}

# 7. Добавить отсылку к PROJECT-CONFIG во все файлы:
$header = "> [!NOTE]`n> **Внимание:** Базовые архитектурные решения (включая выбор БД, шины сообщений, GPS-провайдера и единиц измерения) зафиксированы в `PROJECT-CONFIG.md`. Любые расхождения в данной спецификации следует трактовать в пользу центрального конфига.`n`n"

$filesToHeader = @(
    "d:\MiniTMS\docs\backend\src\application\dto\spec_dto.md",
    "d:\MiniTMS\docs\backend\src\infrastructure\persistence\spec_persistence.md",
    "d:\MiniTMS\docs\backend\messaging\spec_messaging.md",
    "d:\MiniTMS\docs\CHECKLIST.md"
)

foreach ($f in $filesToHeader) {
    if (Test-Path $f) {
        $content = Get-Content -Path $f -Raw
        if ($content -notmatch "PROJECT-CONFIG.md") {
            Set-Content -Path $f -Value ($header + $content) -Encoding UTF8
        }
    }
}
