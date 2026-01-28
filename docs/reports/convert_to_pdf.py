"""
Скрипт для конвертации HTML отчёта в PDF.
Использует библиотеку weasyprint или pdfkit.
"""

import os
import sys

def convert_with_weasyprint(html_path: str, pdf_path: str) -> bool:
    """Конвертация с помощью weasyprint."""
    try:
        from weasyprint import HTML
        HTML(html_path).write_pdf(pdf_path)
        return True
    except ImportError:
        print("weasyprint не установлен")
        return False
    except Exception as e:
        print(f"Ошибка weasyprint: {e}")
        return False

def convert_with_pdfkit(html_path: str, pdf_path: str) -> bool:
    """Конвертация с помощью pdfkit (требует wkhtmltopdf)."""
    try:
        import pdfkit
        pdfkit.from_file(html_path, pdf_path)
        return True
    except ImportError:
        print("pdfkit не установлен")
        return False
    except Exception as e:
        print(f"Ошибка pdfkit: {e}")
        return False

def convert_with_playwright(html_path: str, pdf_path: str) -> bool:
    """Конвертация с помощью Playwright (уже установлен в проекте)."""
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Загружаем HTML файл
            page.goto(f"file:///{html_path.replace(os.sep, '/')}")
            
            # Генерируем PDF
            page.pdf(
                path=pdf_path,
                format="A4",
                margin={"top": "20mm", "bottom": "20mm", "left": "15mm", "right": "15mm"},
                print_background=True
            )
            
            browser.close()
            return True
    except ImportError:
        print("playwright не установлен")
        return False
    except Exception as e:
        print(f"Ошибка playwright: {e}")
        return False

def main():
    # Пути к файлам
    base_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(base_dir, "code_analysis_report.html")
    pdf_path = os.path.join(base_dir, "code_analysis_report.pdf")
    
    print(f"HTML: {html_path}")
    print(f"PDF: {pdf_path}")
    
    if not os.path.exists(html_path):
        print(f"Файл не найден: {html_path}")
        sys.exit(1)
    
    # Пробуем разные методы конвертации
    print("\nПробуем конвертацию с Playwright...")
    if convert_with_playwright(html_path, pdf_path):
        print(f"✅ PDF успешно создан: {pdf_path}")
        return
    
    print("\nПробуем конвертацию с weasyprint...")
    if convert_with_weasyprint(html_path, pdf_path):
        print(f"✅ PDF успешно создан: {pdf_path}")
        return
    
    print("\nПробуем конвертацию с pdfkit...")
    if convert_with_pdfkit(html_path, pdf_path):
        print(f"✅ PDF успешно создан: {pdf_path}")
        return
    
    print("\n❌ Не удалось создать PDF. Установите одну из библиотек:")
    print("   pip install playwright && playwright install chromium")
    print("   или: pip install weasyprint")
    print("   или: pip install pdfkit (+ wkhtmltopdf)")

if __name__ == "__main__":
    main()
