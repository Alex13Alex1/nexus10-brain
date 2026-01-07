import streamlit as st
import subprocess
import os
import sys
import glob
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
#                    🎨 НАСТРОЙКА СТРАНИЦЫ
# ═══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="AI Project Factory v6.0",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Кастомные стили
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .status-box {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .success-box { background-color: #d4edda; border: 1px solid #c3e6cb; }
    .warning-box { background-color: #fff3cd; border: 1px solid #ffeeba; }
    .error-box { background-color: #f8d7da; border: 1px solid #f5c6cb; }
    .info-box { background-color: #d1ecf1; border: 1px solid #bee5eb; }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        font-size: 1.1rem;
        border-radius: 10px;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #764ba2 0%, #667eea 100%);
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#                    📁 ФУНКЦИИ ДЛЯ РАБОТЫ С ПРОЕКТАМИ
# ═══════════════════════════════════════════════════════════════

def get_all_projects():
    """Получает список всех проектов"""
    projects_dir = "./projects"
    if not os.path.exists(projects_dir):
        return []
    projects = []
    for name in os.listdir(projects_dir):
        path = os.path.join(projects_dir, name)
        if os.path.isdir(path):
            mtime = os.path.getmtime(path)
            projects.append({
                "name": name,
                "path": path,
                "modified": datetime.fromtimestamp(mtime)
            })
    return sorted(projects, key=lambda x: x["modified"], reverse=True)


def read_file_safe(filepath):
    """Безопасное чтение файла"""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Ошибка чтения: {e}"
    return None


def run_crew(task_description, api_key=None):
    """Запускает CrewAI через subprocess"""
    env = os.environ.copy()
    if api_key:
        env["OPENAI_API_KEY"] = api_key
    
    process = subprocess.Popen(
        [sys.executable, "main.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        cwd=os.getcwd()
    )
    
    stdout, _ = process.communicate(input=task_description + "\n", timeout=600)
    return stdout, process.returncode


# ═══════════════════════════════════════════════════════════════
#                    🎛️ БОКОВАЯ ПАНЕЛЬ
# ═══════════════════════════════════════════════════════════════

with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/artificial-intelligence.png", width=150)
    st.markdown("## ⚙️ Настройки")
    
    # API Key
    api_key = st.text_input(
        "🔑 OpenAI API Key",
        type="password",
        help="Введите ваш API ключ от OpenAI"
    )
    
    # Выбор модели
    st.markdown("### 🤖 Модели")
    main_model = st.selectbox(
        "Основная модель",
        ["gpt-4o", "gpt-4-turbo", "gpt-4o-mini"],
        help="Модель для сложных задач (архитектура, код)"
    )
    
    fast_model = st.selectbox(
        "Быстрая модель",
        ["gpt-4o-mini", "gpt-3.5-turbo"],
        help="Модель для простых задач (бюджет, QA)"
    )
    
    st.markdown("---")
    
    # Статистика
    st.markdown("### 📊 Статистика")
    projects = get_all_projects()
    col1, col2 = st.columns(2)
    col1.metric("Проектов", len(projects))
    col2.metric("Агентов", 7)
    
    st.markdown("---")
    st.markdown("### 🔗 Ссылки")
    st.markdown("- [CrewAI Docs](https://docs.crewai.com)")
    st.markdown("- [OpenAI Platform](https://platform.openai.com)")

# ═══════════════════════════════════════════════════════════════
#                    🏠 ГЛАВНАЯ СТРАНИЦА
# ═══════════════════════════════════════════════════════════════

st.markdown('<p class="main-header">🚀 AI Project Factory v6.0</p>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: gray;">Автономная система генерации проектов с 7 AI-агентами</p>', unsafe_allow_html=True)

# Табы
tab1, tab2, tab3, tab4 = st.tabs(["🛠️ Новый проект", "📁 Мои проекты", "📊 Мониторинг", "📖 Документация"])

# ═══════════════════════════════════════════════════════════════
#                    TAB 1: НОВЫЙ ПРОЕКТ
# ═══════════════════════════════════════════════════════════════

with tab1:
    st.markdown("### 💡 Опиши свою идею")
    
    # Примеры задач
    example_tasks = [
        "Выбери пример или напиши свой...",
        "Telegram бот для отслеживания криптовалют",
        "REST API для управления задачами с авторизацией",
        "Парсер новостей с сохранением в базу данных",
        "Калькулятор с графическим интерфейсом",
        "Генератор паролей с разными уровнями сложности",
        "URL сокращатель с кастомными алиасами",
        "Инструмент шифрования файлов AES-256"
    ]
    
    selected_example = st.selectbox("📝 Примеры задач:", example_tasks)
    
    user_input = st.text_area(
        "Описание проекта:",
        value="" if selected_example == example_tasks[0] else selected_example,
        placeholder="Например: Создай мессенджер на Flask с шифрованием AES-256",
        height=150
    )
    
    # Дополнительные опции
    with st.expander("⚙️ Дополнительные настройки"):
        col1, col2 = st.columns(2)
        with col1:
            use_memory = st.checkbox("🧠 Использовать память", value=True)
            auto_install = st.checkbox("📦 Авто-установка зависимостей", value=True)
        with col2:
            self_healing = st.checkbox("🔄 Self-Healing режим", value=True)
            create_diagram = st.checkbox("🎨 Создать Mermaid диаграмму", value=True)
    
    # Кнопка запуска
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        run_button = st.button("🚀 Запустить производство", use_container_width=True)
    
    if run_button:
        if not user_input or user_input == example_tasks[0]:
            st.warning("⚠️ Сначала введи описание задачи!")
        elif not api_key:
            st.warning("⚠️ Введите API ключ в боковой панели!")
        else:
            with st.spinner("🔄 Агенты работают... Это может занять несколько минут."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                stages = [
                    "💰 Cost Optimizer анализирует задачу...",
                    "🔍 Tech Researcher исследует технологии...",
                    "🏗️ Architect проектирует систему...",
                    "🎨 Visualizer создает диаграмму...",
                    "🔧 Engineer подбирает стек...",
                    "👨‍💻 Developer пишет код...",
                    "🔍 QA Engineer тестирует...",
                    "🔄 Self-Healing исправляет ошибки...",
                    "✅ Финальная проверка..."
                ]
                
                try:
                    output, return_code = run_crew(user_input, api_key)
                    
                    if return_code == 0:
                        progress_bar.progress(100)
                        st.success("✅ Проект успешно создан!")
                        
                        # Показать последний проект
                        projects = get_all_projects()
                        if projects:
                            latest = projects[0]
                            st.info(f"📁 Проект сохранен: `{latest['path']}`")
                            
                            with st.expander("📜 Лог выполнения"):
                                st.code(output[-5000:] if len(output) > 5000 else output)
                    else:
                        st.error("❌ Произошла ошибка при создании проекта")
                        with st.expander("🔍 Подробности ошибки"):
                            st.code(output)
                            
                except subprocess.TimeoutExpired:
                    st.error("⏰ Превышен лимит времени (10 минут)")
                except Exception as e:
                    st.error(f"❌ Ошибка: {str(e)}")

# ═══════════════════════════════════════════════════════════════
#                    TAB 2: МОИ ПРОЕКТЫ
# ═══════════════════════════════════════════════════════════════

with tab2:
    st.markdown("### 📁 Созданные проекты")
    
    projects = get_all_projects()
    
    if not projects:
        st.info("📭 Пока нет созданных проектов. Создай первый во вкладке 'Новый проект'!")
    else:
        # Поиск
        search = st.text_input("🔍 Поиск проекта:", placeholder="Введите название...")
        
        filtered = [p for p in projects if search.lower() in p["name"].lower()] if search else projects
        
        for project in filtered:
            with st.expander(f"📂 {project['name']} — {project['modified'].strftime('%d.%m.%Y %H:%M')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📄 Файлы проекта:**")
                    
                    # Архитектура
                    arch_file = os.path.join(project["path"], "docs", "architecture.md")
                    if content := read_file_safe(arch_file):
                        with st.expander("📄 Архитектура"):
                            st.markdown(content)
                    
                    # Код
                    code_file = os.path.join(project["path"], "source_code", "main_fixed.py")
                    if not os.path.exists(code_file):
                        code_file = os.path.join(project["path"], "source_code", "main.py")
                    if content := read_file_safe(code_file):
                        with st.expander("💻 Исходный код"):
                            st.code(content, language="python")
                
                with col2:
                    # Диаграмма
                    diagram_file = os.path.join(project["path"], "diagrams", "architecture.md")
                    if content := read_file_safe(diagram_file):
                        st.markdown("**🎨 Диаграмма:**")
                        st.code(content, language="markdown")
                    
                    # QA отчет
                    qa_file = os.path.join(project["path"], "tests", "final_report.md")
                    if not os.path.exists(qa_file):
                        qa_file = os.path.join(project["path"], "tests", "review_report.md")
                    if content := read_file_safe(qa_file):
                        with st.expander("🧪 QA Отчет"):
                            st.markdown(content)
                
                # Кнопки действий
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"📂 Открыть папку", key=f"open_{project['name']}"):
                        os.startfile(project["path"]) if sys.platform == "win32" else None
                with col2:
                    code_path = os.path.join(project["path"], "source_code", "main_fixed.py")
                    if os.path.exists(code_path):
                        if st.button(f"▶️ Запустить код", key=f"run_{project['name']}"):
                            result = subprocess.run(
                                [sys.executable, code_path],
                                capture_output=True, text=True, timeout=30
                            )
                            if result.returncode == 0:
                                st.success("✅ Код выполнен!")
                                st.code(result.stdout)
                            else:
                                st.error("❌ Ошибка выполнения")
                                st.code(result.stderr)

# ═══════════════════════════════════════════════════════════════
#                    TAB 3: МОНИТОРИНГ
# ═══════════════════════════════════════════════════════════════

with tab3:
    st.markdown("### 📊 Мониторинг системы")
    
    # Метрики
    col1, col2, col3, col4 = st.columns(4)
    
    projects = get_all_projects()
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h2>📁 {}</h2>
            <p>Проектов</p>
        </div>
        """.format(len(projects)), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h2>👥 7</h2>
            <p>Агентов</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h2>📋 10</h2>
            <p>Задач</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h2>🧠 ON</h2>
            <p>Память</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Последний проект
    if projects:
        latest = projects[0]
        st.markdown(f"### 🕐 Последний проект: `{latest['name']}`")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Архитектура")
            diagram_file = os.path.join(latest["path"], "diagrams", "architecture.md")
            if content := read_file_safe(diagram_file):
                st.code(content, language="markdown")
            else:
                st.info("Диаграмма не найдена")
        
        with col2:
            st.markdown("#### 📝 QA Отчет")
            qa_file = os.path.join(latest["path"], "tests", "final_report.md")
            if not os.path.exists(qa_file):
                qa_file = os.path.join(latest["path"], "tests", "review_report.md")
            if content := read_file_safe(qa_file):
                st.markdown(content)
            else:
                st.info("QA отчет не найден")
    
    # Pipeline визуализация
    st.markdown("---")
    st.markdown("### 🔄 Pipeline агентов")
    st.markdown("""
    ```
    ┌──────────────────────────────────────────────────────────────────┐
    │  0. 💰 Cost Optimizer    → Анализ затрат                         │
    │  1. 🔍 Tech Researcher   → Исследование технологий               │
    │  2. 🏗️  Architect         → Архитектура                          │
    │  3. 🎨 Visualizer        → Mermaid диаграммы                     │
    │  4. 🔧 Engineer          → Технологический стек                  │
    │  5. 👨‍💻 Developer         → Написание кода                        │
    │  6. 📦 Developer         → Requirements.txt                      │
    │  7. 🔍 QA Engineer       → Первичное тестирование                │
    │  8. 🔄 Developer         → Self-Healing (исправления)            │
    │  9. ✅ QA Engineer       → Финальная проверка                    │
    │  +  📦 Auto-Installer    → Установка зависимостей                │
    └──────────────────────────────────────────────────────────────────┘
    ```
    """)

# ═══════════════════════════════════════════════════════════════
#                    TAB 4: ДОКУМЕНТАЦИЯ
# ═══════════════════════════════════════════════════════════════

with tab4:
    st.markdown("### 📖 Документация системы")
    
    st.markdown("""
    ## 🚀 AI Project Factory v6.0
    
    Автономная система генерации проектов с использованием 7 AI-агентов.
    
    ### 👥 Агенты
    
    | Агент | Роль | Модель |
    |-------|------|--------|
    | 💰 Cost Optimizer | Анализ затрат и сложности | gpt-4o-mini |
    | 🔍 Tech Researcher | Исследование технологий | gpt-4o-mini |
    | 🏗️ Architect | Проектирование архитектуры | gpt-4o |
    | 🎨 Visualizer | Создание Mermaid диаграмм | gpt-4o |
    | 🔧 Engineer | Подбор технологического стека | gpt-4o |
    | 👨‍💻 Developer | Написание кода | gpt-4o |
    | 🔍 QA Engineer | Тестирование и запуск кода | gpt-4o-mini |
    
    ### 🔧 Функции
    
    - **🧠 Memory (RAG)** — Агенты помнят прошлые решения
    - **💰 Cost Optimization** — Разные модели для разных задач
    - **🔄 Self-Healing** — Автоматическое исправление ошибок
    - **📦 Auto-Install** — Автоустановка зависимостей
    - **🎨 Visualize** — Генерация Mermaid диаграмм
    - **🔍 Research** — Исследование актуальных технологий
    
    ### 📁 Структура проекта
    
    ```
    projects/[project_name]/
    ├── reports/
    │   ├── cost_analysis.md      # Анализ затрат
    │   └── tech_research.md      # Исследование технологий
    ├── docs/
    │   └── architecture.md       # Архитектура
    ├── diagrams/
    │   └── architecture.md       # Mermaid диаграмма
    ├── tech_specs/
    │   └── technology_stack.md   # Технологический стек
    ├── source_code/
    │   ├── main.py               # Первоначальный код
    │   ├── main_fixed.py         # Исправленный код
    │   └── requirements.txt      # Зависимости
    └── tests/
        ├── review_report.md      # Первичный QA
        └── final_report.md       # Финальный QA
    ```
    
    ### 🚀 Запуск
    
    ```bash
    # Консольный режим
    python main.py
    
    # Web-интерфейс
    streamlit run gui_panel.py
    ```
    """)

# ═══════════════════════════════════════════════════════════════
#                    🦶 FOOTER
# ═══════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: gray;">AI Project Factory v6.0 | Powered by CrewAI + OpenAI | 2026</p>',
    unsafe_allow_html=True
)


