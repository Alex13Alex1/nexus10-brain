import streamlit as st
import subprocess
import os
import sys
import time
import json
from datetime import datetime
from PIL import Image
import io

# Добавляем путь к модулям
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Импорт модулей AI Factory v0.95 THE NEXUS HIVE
try:
    from tools import (
        check_docker_available,
        deploy_docker,
        stop_docker,
        check_system_health,
        read_file_safe,
        install_dependencies
    )
    from core_engine import (
        run_ai_factory, 
        setup_workspace, 
        SPECIALIST_CATALOG,
        spawn_specialist,
        SwarmEngine,
        start_swarm_production,
        SwarmMaster,          # 🆕 v0.95
        run_nexus_hive        # 🆕 v0.95
    )
    from observer import Observer, quick_check
    MODULES_AVAILABLE = True
    SWARM_MASTER_AVAILABLE = True
except ImportError as e:
    MODULES_AVAILABLE = False
    SWARM_MASTER_AVAILABLE = False
    SPECIALIST_CATALOG = {}
    print(f"⚠️ Modules not fully loaded: {e}")

# ═══════════════════════════════════════════════════════════════
#                    🎨 НАСТРОЙКА СТРАНИЦЫ
# ═══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="AI Factory v0.95 HIVE",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Кастомные стили
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Space+Grotesk:wght@400;700&display=swap');
    
    .main-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .subtitle {
        text-align: center;
        color: #888;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .vision-box {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 1rem 0;
    }
    .metric-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .success-banner {
        background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        font-weight: bold;
    }
    .stButton>button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        border-radius: 25px;
        font-weight: bold;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
    }
    .upload-area {
        border: 2px dashed #667eea;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        background: rgba(102, 126, 234, 0.05);
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#                    📁 ФУНКЦИИ
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
        except:
            return None
    return None


def check_docker_available():
    """Проверяет доступность Docker"""
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except:
        return False


def deploy_locally(project_path):
    """Собирает и запускает Docker контейнер"""
    deploy_path = os.path.join(project_path, "deploy")
    
    # Проверяем наличие файлов
    dockerfile = os.path.join(deploy_path, "Dockerfile")
    compose_file = os.path.join(deploy_path, "docker-compose.yml")
    
    if not os.path.exists(dockerfile):
        return False, "❌ Dockerfile не найден"
    
    # Копируем исходники в deploy для сборки
    source_code = os.path.join(project_path, "source_code")
    if os.path.exists(source_code):
        import shutil
        for f in os.listdir(source_code):
            src = os.path.join(source_code, f)
            dst = os.path.join(deploy_path, f)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
    
    try:
        # Сначала останавливаем старые контейнеры
        subprocess.run(
            ["docker-compose", "down"],
            cwd=deploy_path,
            capture_output=True,
            timeout=30
        )
        
        # Собираем и запускаем
        result = subprocess.run(
            ["docker-compose", "up", "--build", "-d"],
            cwd=deploy_path,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            return True, "✅ Контейнер запущен!"
        else:
            return False, f"❌ Ошибка сборки:\n{result.stderr}"
            
    except subprocess.TimeoutExpired:
        return False, "⏰ Превышен таймаут сборки (5 мин)"
    except Exception as e:
        return False, f"❌ Ошибка: {str(e)}"


def stop_container(project_path):
    """Останавливает контейнер проекта"""
    deploy_path = os.path.join(project_path, "deploy")
    try:
        result = subprocess.run(
            ["docker-compose", "down"],
            cwd=deploy_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except:
        return False


def get_container_status(project_path):
    """Проверяет статус контейнера"""
    deploy_path = os.path.join(project_path, "deploy")
    try:
        result = subprocess.run(
            ["docker-compose", "ps", "--format", "json"],
            cwd=deploy_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.stdout.strip():
            return "running"
        return "stopped"
    except:
        return "unknown"


def run_factory(goal, has_image=False, enable_swarm=True, use_hierarchical=True):
    """Запускает фабрику агентов v0.95 THE NEXUS HIVE"""
    
    # Try direct import first (faster, more reliable)
    if MODULES_AVAILABLE:
        try:
            import io
            from contextlib import redirect_stdout, redirect_stderr
            
            # Capture output
            output_buffer = io.StringIO()
            
            with redirect_stdout(output_buffer), redirect_stderr(output_buffer):
                image_path = "temp_vision.png" if has_image else None
                
                # 🐝 Use SwarmMaster for v0.95 (The Nexus Hive)
                if enable_swarm and use_hierarchical and SWARM_MASTER_AVAILABLE:
                    # NEW! SwarmMaster - система сначала думает, кто ей нужен
                    workspace, result = run_nexus_hive(goal)
                elif enable_swarm:
                    # Fallback to SwarmEngine
                    workspace, result = start_swarm_production(goal, hierarchical=use_hierarchical)
                else:
                    # Classic mode
                    workspace, result = run_ai_factory(goal, image_path=image_path, enable_swarm=enable_swarm)
            
            output = output_buffer.getvalue()
            return output + f"\n\n✅ Project created at: {workspace}", 0
            
        except Exception as e:
            import traceback
            return f"❌ Direct import failed: {str(e)}\n{traceback.format_exc()}", 1
    
    # Fallback to subprocess
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    # Pass swarm mode via environment variable
    env["NEXUS_SWARM_MODE"] = "1" if enable_swarm else "0"
    env["NEXUS_HIERARCHICAL"] = "1" if use_hierarchical else "0"
    
    process = subprocess.Popen(
        [sys.executable, "-c", f"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from core_engine import run_nexus_hive, run_ai_factory
if {enable_swarm} and {use_hierarchical}:
    run_nexus_hive('''{goal}''')
else:
    run_ai_factory('''{goal}''', enable_swarm={enable_swarm})
"""],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        cwd=os.getcwd()
    )
    
    stdout, _ = process.communicate(timeout=900)
    return stdout, process.returncode


# ═══════════════════════════════════════════════════════════════
#                    🎛️ БОКОВАЯ ПАНЕЛЬ
# ═══════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 🧠 AI Factory Nexus")
    st.markdown("---")
    
    projects = get_all_projects()
    
    st.markdown("### 📊 Статистика")
    col1, col2 = st.columns(2)
    col1.metric("📁 Проектов", len(projects))
    col2.metric("👥 Агентов", "8+")
    
    # Docker status
    try:
        docker_ok = check_docker_available() if MODULES_AVAILABLE else False
    except:
        docker_ok = False
    st.markdown(f"🐳 Docker: {'✅ Готов' if docker_ok else '❌ Недоступен'}")
    st.markdown(f"📦 Modules: {'✅ Loaded' if MODULES_AVAILABLE else '⚠️ Partial'}")
    
    st.markdown("---")
    
    st.markdown("### 🧠 v0.95 THE NEXUS HIVE")
    st.markdown("""
    **SwarmMaster Architecture:**
    - 🧠 **Strategic Dispatcher** — Мозг системы 🆕
    - 🏗️ **Nexus Architect** — System Design
    - 👨‍💻 **Lead Developer** — Code
    - 🔐 **Security Auditor** — Kill Switch
    - 🏥 **SRE Observer** — Deploy
    
    **🐝 Dynamic Expert Spawning:**
    Система САМА решает, какие эксперты нужны!
    
    `Data Scientist` `UX Designer`
    `Security Expert` `DevOps Engineer`
    `Database Architect` `Mobile Dev`
    `Blockchain Dev` `QA Automation`
    
    **Возможности:**
    - 🧠 **Strategic Dispatch** — 🆕
    - 🐝 **Auto Expert Hiring** — 🆕
    - 🔄 **Process.hierarchical**
    - 🛑 **Kill Switch** — Emergency Stop
    - 📊 **Dynamic Task Generation**
    """)
    
    st.markdown("---")
    
    st.markdown("### 👥 Агенты v1.0")
    agents = [
        ("🐝", "Swarm Manager", "4o", "NEW!"),
        ("🔍", "Tech Researcher", "mini", ""),
        ("🏗️", "Architect", "4o", ""),
        ("👨‍💻", "Developer", "4o", ""),
        ("🧪", "QA Engineer", "4o", ""),
        ("🎓", "Performance Mentor", "4o", ""),
        ("🔐", "Security Auditor", "4o", ""),
        ("🏥", "SRE Observer", "mini", ""),
    ]
    
    for icon, name, model, badge in agents:
        badge_html = f" 🆕" if badge else ""
        st.markdown(f"{icon} **{name}** `{model}`{badge_html}")
    
    st.markdown("---")
    st.markdown("### 🐝 Dynamic Specialists")
    st.markdown("`On-demand spawning`")


# ═══════════════════════════════════════════════════════════════
#                    🏠 ГЛАВНАЯ СТРАНИЦА
# ═══════════════════════════════════════════════════════════════

st.markdown('<p class="main-title">🧠 THE NEXUS HIVE</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">v0.95 • SwarmMaster • Система сначала думает, кто ей нужен</p>', unsafe_allow_html=True)

# Метрики
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="metric-box">
        <div class="metric-value">8+</div>
        <div class="metric-label">🐝 Swarm</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-box">
        <div class="metric-value">10</div>
        <div class="metric-label">📋 Задач</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-value">{len(projects)}</div>
        <div class="metric-label">📁 Проектов</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="metric-box">
        <div class="metric-value">👁️</div>
        <div class="metric-label">Vision ON</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Главный интерфейс
col_input, col_status = st.columns([1, 1])

with col_input:
    st.markdown("### ⚙️ Параметры проекта")
    
    # 👁️ ЗАГРУЗКА ИЗОБРАЖЕНИЯ (НОВОЕ!)
    st.markdown("#### 👁️ Визуальный ввод (опционально)")
    
    uploaded_file = st.file_uploader(
        "Загрузи скриншот, схему или набросок идеи",
        type=['png', 'jpg', 'jpeg', 'gif', 'webp'],
        help="Vision Analyst проанализирует изображение и создаст ТЗ"
    )
    
    has_image = False
    if uploaded_file:
        # Показываем превью
        image = Image.open(uploaded_file)
        st.image(image, caption='👁️ Загруженное изображение', use_container_width=True)
        
        # Сохраняем для агентов
        with open("temp_vision.png", "wb") as f:
            f.write(uploaded_file.getbuffer())
        has_image = True
        
        st.markdown('<div class="vision-box">✅ Vision Analyst проанализирует это изображение!</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Примеры
    examples = [
        "Выбери пример...",
        "REST API для управления задачами",
        "Telegram бот для отслеживания криптовалют",
        "Дашборд с графиками и метриками",
        "Форма регистрации с валидацией",
        "Калькулятор с красивым UI",
        "Лендинг для стартапа",
        "Админ-панель для магазина"
    ]
    
    selected = st.selectbox("📝 Примеры задач:", examples)
    
    goal = st.text_area(
        "🎯 Что должна делать программа?",
        value="" if selected == examples[0] else selected,
        height=120,
        placeholder="Опиши задачу... Если загрузил картинку — напиши что на ней."
    )
    
    # 🧠 NEXUS HIVE MODE
    st.markdown("#### 🧠 The Nexus Hive v0.95")
    
    enable_swarm = st.checkbox(
        "🐝 Включить динамическое роение", 
        value=True,
        help="Strategic Dispatcher проанализирует задачу и наймет нужных экспертов"
    )
    
    use_hierarchical = st.checkbox(
        "🔄 Hierarchical Process (SwarmMaster)",
        value=True,
        help="Manager LLM координирует всех агентов. Система сначала ДУМАЕТ, кто ей нужен."
    )
    
    if enable_swarm:
        mode_text = "NEXUS HIVE" if use_hierarchical else "SWARM ENGINE"
        st.info(f"🧠 **{mode_text}** | Эксперты будут наняты автоматически!")
        
        # Показать процесс
        with st.expander("🔍 Как работает SwarmMaster?"):
            st.markdown("""
            **Этап 1: Strategic Dispatch**
            - Анализ мультизадачи
            - Определение 3-5 критических ролей
            - Вывод JSON-конфигурации роя
            
            **Этап 2: Expert Spawning**
            - Динамическое создание агентов
            - Каждый эксперт получает цель и бекстори
            
            **Этап 3: Production**
            - Process.hierarchical
            - Manager LLM координирует всех
            - Финальная сборка проекта
            """)
    
    # Опции
    with st.expander("⚙️ Дополнительные настройки"):
        col1, col2 = st.columns(2)
        with col1:
            use_memory = st.checkbox("🧠 Память", value=True)
            self_heal = st.checkbox("🔄 Self-Healing", value=True)
        with col2:
            gen_docker = st.checkbox("🐳 Docker", value=True)
            gen_readme = st.checkbox("📝 README", value=True)
    
    # Кнопка запуска
    if enable_swarm and use_hierarchical:
        button_text = "🧠 ЗАПУСТИТЬ NEXUS HIVE"
    elif enable_swarm:
        button_text = "🐝 ЗАПУСТИТЬ SWARM"
    elif has_image:
        button_text = "🚀 ЗАПУСТИТЬ С VISION"
    else:
        button_text = "🚀 ЗАПУСТИТЬ ПРОИЗВОДСТВО"
    
    if st.button(button_text, use_container_width=True):
        if not goal or goal == examples[0]:
            st.error("⚠️ Введите описание проекта!")
        else:
            progress_bar = st.progress(0)
            
            swarm_text = " 🧠 NEXUS HIVE анализирует и нанимает экспертов..." if (enable_swarm and use_hierarchical) else (" 🐝 Swarm..." if enable_swarm else "")
            with st.spinner("🔄 " + swarm_text + (" 👁️ Vision анализирует изображение..." if has_image else "")):
                try:
                    output, return_code = run_factory(goal, has_image, enable_swarm, use_hierarchical)
                    
                    progress_bar.progress(100)
                    
                    if return_code == 0:
                        st.markdown('<div class="success-banner">✅ ПРОЕКТ УСПЕШНО СОЗДАН!</div>', unsafe_allow_html=True)
                        st.balloons()
                        
                        new_projects = get_all_projects()
                        if new_projects:
                            latest = new_projects[0]
                            st.success(f"📁 Проект: `{latest['path']}`")
                            
                            # Показать визуальный анализ если был
                            if has_image:
                                vision_file = os.path.join(latest["path"], "vision", "visual_analysis.md")
                                if content := read_file_safe(vision_file):
                                    with st.expander("👁️ Визуальный анализ"):
                                        st.markdown(content)
                    else:
                        st.error("❌ Произошла ошибка")
                    
                    with st.expander("📜 Лог выполнения"):
                        st.code(output[-10000:] if len(output) > 10000 else output)
                        
                except subprocess.TimeoutExpired:
                    st.error("⏰ Превышен лимит времени")
                except Exception as e:
                    st.error(f"❌ Ошибка: {str(e)}")

with col_status:
    st.markdown("### 📊 Результаты")
    
    projects = get_all_projects()
    
    if projects:
        latest = projects[0]
        st.info(f"📂 Последний проект: **{latest['name']}**")
        
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["🐝 Swarm", "👁️ Vision", "🎨 Диаграмма", "💻 Код", "🧪 QA", "🐳 Docker", "🏥 SRE", "📝 README"])
        
        with tab1:
            # 🐝 SWARM ANALYSIS
            swarm_file = os.path.join(latest["path"], "swarm", "analysis.json")
            if os.path.exists(swarm_file):
                try:
                    with open(swarm_file, 'r', encoding='utf-8') as f:
                        swarm_data = json.load(f)
                    
                    st.markdown("### 🐝 Swarm Analysis")
                    
                    complexity = swarm_data.get('complexity', 'UNKNOWN')
                    color_map = {'LOW': '🟢', 'MEDIUM': '🟡', 'HIGH': '🟠', 'EXTREME': '🔴'}
                    color = color_map.get(complexity, '⚪')
                    
                    st.markdown(f"**Complexity:** {color} {complexity}")
                    
                    specialists = swarm_data.get('required_specialists', [])
                    if specialists:
                        st.markdown(f"**Spawned Specialists:** {len(specialists)}")
                        for spec in specialists:
                            desc = SPECIALIST_CATALOG.get(spec, spec)
                            st.markdown(f"• 🐝 `{spec}` — {desc}")
                    else:
                        st.info("No additional specialists were needed")
                    
                    if reasoning := swarm_data.get('reasoning'):
                        st.markdown(f"**Reasoning:** {reasoning}")
                    
                    # Show specialist reports
                    swarm_dir = os.path.join(latest["path"], "swarm")
                    for spec in specialists:
                        report_file = os.path.join(swarm_dir, f"{spec}_report.md")
                        if content := read_file_safe(report_file):
                            with st.expander(f"📄 {spec.upper()} Expert Report"):
                                st.markdown(content)
                except Exception as e:
                    st.error(f"Error loading swarm analysis: {e}")
            else:
                st.info("🐝 Swarm Mode was disabled or analysis not available")
        
        with tab2:
            vision_file = os.path.join(latest["path"], "vision", "visual_analysis.md")
            if content := read_file_safe(vision_file):
                st.markdown("**👁️ Визуальный анализ:**")
                st.markdown(content)
            else:
                st.info("Визуальный анализ не выполнялся (не было изображения)")
        
        with tab3:
            diagram_file = os.path.join(latest["path"], "diagrams", "architecture.md")
            if not os.path.exists(diagram_file):
                diagram_file = os.path.join(latest["path"], "docs", "architecture.md")
            if content := read_file_safe(diagram_file):
                st.code(content, language="markdown")
            else:
                st.info("Диаграмма не найдена")
        
        with tab4:
            code_file = os.path.join(latest["path"], "source_code", "main_fixed.py")
            if not os.path.exists(code_file):
                code_file = os.path.join(latest["path"], "source_code", "main.py")
            if content := read_file_safe(code_file):
                st.code(content, language="python")
                
                if st.button("▶️ Запустить код"):
                    try:
                        result = subprocess.run(
                            [sys.executable, code_file],
                            capture_output=True, text=True, timeout=30
                        )
                        if result.returncode == 0:
                            st.success("✅ Выполнено!")
                            st.code(result.stdout)
                        else:
                            st.error("❌ Ошибка")
                            st.code(result.stderr)
                    except Exception as e:
                        st.error(f"Ошибка: {e}")
            else:
                st.info("Код не найден")
        
        with tab5:
            qa_file = os.path.join(latest["path"], "tests", "final_report.md")
            if not os.path.exists(qa_file):
                qa_file = os.path.join(latest["path"], "tests", "qa_report.md")
            if not os.path.exists(qa_file):
                qa_file = os.path.join(latest["path"], "tests", "review_report.md")
            if content := read_file_safe(qa_file):
                st.markdown(content)
            else:
                st.info("QA отчет не найден")
        
        with tab6:
            docker_file = os.path.join(latest["path"], "deploy", "Dockerfile")
            if not os.path.exists(docker_file):
                docker_file = os.path.join(latest["path"], "deployment", "Dockerfile")
            if content := read_file_safe(docker_file):
                st.code(content, language="dockerfile")
                
                compose_file = os.path.join(latest["path"], "deploy", "docker-compose.yml")
                if compose := read_file_safe(compose_file):
                    st.markdown("**docker-compose.yml:**")
                    st.code(compose, language="yaml")
                
                # 🌐 КНОПКА ЖИВОГО ЗАПУСКА
                st.markdown("---")
                st.markdown("### 🚀 Деплой")
                
                docker_available = check_docker_available()
                
                if not docker_available:
                    st.warning("⚠️ Docker не установлен или не запущен")
                else:
                    col_deploy, col_stop = st.columns(2)
                    
                    with col_deploy:
                        if st.button("🌐 Deploy (Запустить)", use_container_width=True, key="deploy_btn"):
                            with st.spinner("🔨 Собираю Docker образ... (до 5 мин)"):
                                success, message = deploy_locally(latest["path"])
                                if success:
                                    st.success(message)
                                    st.markdown("""
                                    🎉 **Приложение запущено!**
                                    
                                    Попробуй открыть:
                                    - `http://localhost:8080`
                                    - `http://localhost:8000`
                                    - `http://localhost:5000`
                                    
                                    *(порт зависит от настроек проекта)*
                                    """)
                                    st.balloons()
                                else:
                                    st.error(message)
                    
                    with col_stop:
                        if st.button("⏹️ Stop (Остановить)", use_container_width=True, key="stop_btn"):
                            if stop_container(latest["path"]):
                                st.success("✅ Контейнер остановлен")
                            else:
                                st.warning("Контейнер не запущен")
                    
                    # Показать Makefile если есть
                    makefile = os.path.join(latest["path"], "Makefile")
                    if makefile_content := read_file_safe(makefile):
                        with st.expander("📜 Makefile"):
                            st.code(makefile_content, language="makefile")
                    
                    # CI/CD
                    ci_file = os.path.join(latest["path"], "deploy", "ci.yml")
                    if ci_content := read_file_safe(ci_file):
                        with st.expander("⚙️ GitHub Actions CI/CD"):
                            st.code(ci_content, language="yaml")
                            st.info("📋 Скопируй в `.github/workflows/ci.yml`")
            else:
                st.info("Dockerfile не найден")
        
        with tab7:
            st.markdown("### 🏥 SRE Monitoring & Self-Healing")
            
            # ═══════════════════════════════════════════════════════════
            #                    💓 ЖИВОЙ ПУЛЬС ПРОЕКТА
            # ═══════════════════════════════════════════════════════════
            
            st.markdown("#### 💓 Пульс проекта (Live Status)")
            
            # Читаем live status
            live_status_file = os.path.join(latest["path"], "monitoring", "live_status.json")
            live_status = None
            
            if os.path.exists(live_status_file):
                try:
                    import json
                    with open(live_status_file, 'r', encoding='utf-8') as f:
                        live_status = json.load(f)
                except:
                    pass
            
            # Метрики статуса
            col_docker, col_http, col_logs, col_overall = st.columns(4)
            
            if live_status:
                with col_docker:
                    docker_status = live_status.get("docker", "unknown")
                    docker_emoji = "🟢" if docker_status == "healthy" else "🔴" if docker_status in ["crashed", "unavailable"] else "🟡"
                    st.metric("🐳 Docker", docker_status.upper(), delta=docker_emoji)
                
                with col_http:
                    http_status = live_status.get("http", "unknown")
                    http_emoji = "🟢" if http_status == "healthy" else "🔴" if http_status == "unreachable" else "🟡"
                    st.metric("🌐 HTTP", http_status.upper(), delta=http_emoji)
                
                with col_logs:
                    logs_status = live_status.get("logs", "unknown")
                    logs_emoji = "🟢" if logs_status == "clean" else "🔴" if logs_status == "errors_found" else "🟡"
                    st.metric("📜 Logs", logs_status.upper(), delta=logs_emoji)
                
                with col_overall:
                    overall = live_status.get("overall", "unknown")
                    if overall == "healthy":
                        st.success(f"🟢 HEALTHY")
                    elif overall == "degraded":
                        st.warning(f"🟡 DEGRADED")
                    elif overall == "critical":
                        st.error(f"🔴 CRITICAL")
                    else:
                        st.info(f"⚪ {overall.upper()}")
                
                # Время последней проверки
                timestamp = live_status.get("timestamp", "N/A")
                st.caption(f"⏰ Последняя проверка: {timestamp}")
                
                # Ошибки если есть
                if live_status.get("errors"):
                    st.error("🚨 Обнаруженные проблемы:")
                    for err in live_status["errors"]:
                        st.markdown(f"- {err}")
                
                # Действия если были
                if live_status.get("actions_taken"):
                    st.info("🔧 Выполненные действия:")
                    for action in live_status["actions_taken"]:
                        st.markdown(f"- {action}")
            else:
                col_docker.metric("🐳 Docker", "N/A")
                col_http.metric("🌐 HTTP", "N/A")
                col_logs.metric("📜 Logs", "N/A")
                col_overall.info("⚪ Не мониторится")
                st.info("💡 Запустите проект и деплой для активации мониторинга")
            
            st.markdown("---")
            
            # ═══════════════════════════════════════════════════════════
            #                    🔄 ПАНЕЛЬ УПРАВЛЕНИЯ
            # ═══════════════════════════════════════════════════════════
            
            st.markdown("#### 🔄 Панель управления")
            
            col_check, col_heal, col_restart = st.columns(3)
            
            with col_check:
                if st.button("🔍 Проверить здоровье", key="check_health", use_container_width=True):
                    with st.spinner("Проверка..."):
                        try:
                            # Docker status
                            docker_result = subprocess.run(
                                ["docker", "ps", "-a", "--filter", "name=app", "--format", "{{.Names}}: {{.Status}}"],
                                capture_output=True, text=True, timeout=10
                            )
                            
                            # HTTP check
                            http_status = "❌ Unreachable"
                            try:
                                import urllib.request
                                with urllib.request.urlopen("http://localhost:8080", timeout=3) as r:
                                    http_status = f"✅ HTTP {r.getcode()}"
                            except:
                                pass
                            
                            st.success("Проверка завершена!")
                            st.code(f"Docker: {docker_result.stdout or 'No containers'}\nHTTP: {http_status}")
                        except Exception as e:
                            st.error(f"Ошибка: {e}")
            
            with col_heal:
                if st.button("💊 Запустить исцеление", key="run_healing", use_container_width=True):
                    with st.spinner("Запуск self-healing..."):
                        try:
                            # Restart container
                            result = subprocess.run(
                                ["docker-compose", "restart"],
                                cwd=os.path.join(latest["path"], "deploy"),
                                capture_output=True, text=True, timeout=60
                            )
                            if result.returncode == 0:
                                st.success("✅ Контейнер перезапущен!")
                            else:
                                st.warning(f"⚠️ {result.stderr}")
                        except Exception as e:
                            st.error(f"Ошибка: {e}")
            
            with col_restart:
                if st.button("🔄 Пересобрать", key="rebuild", use_container_width=True):
                    with st.spinner("Пересборка Docker образа..."):
                        try:
                            result = subprocess.run(
                                ["docker-compose", "up", "--build", "-d"],
                                cwd=os.path.join(latest["path"], "deploy"),
                                capture_output=True, text=True, timeout=300
                            )
                            if result.returncode == 0:
                                st.success("✅ Образ пересобран и запущен!")
                            else:
                                st.error(f"❌ {result.stderr}")
                        except Exception as e:
                            st.error(f"Ошибка: {e}")
            
            st.markdown("---")
            
            # ═══════════════════════════════════════════════════════════
            #                    🔄 THE LOOP - Continuous Improvement
            # ═══════════════════════════════════════════════════════════
            
            st.markdown("#### 🔄 THE LOOP - Непрерывное улучшение")
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 10px; color: white; margin-bottom: 1rem;">
                <b>Observer → Analyzer → Coder → DevOps → Deploy → Observer</b><br>
                Автоматический цикл мониторинга и самоисцеления
            </div>
            """, unsafe_allow_html=True)
            
            col_loop1, col_loop2, col_loop3 = st.columns([2, 1, 1])
            
            with col_loop1:
                loop_interval = st.slider(
                    "Интервал проверки (секунд)", 
                    min_value=60, 
                    max_value=600, 
                    value=300, 
                    step=60,
                    key="loop_interval"
                )
            
            with col_loop2:
                loop_iterations = st.number_input(
                    "Итераций",
                    min_value=1,
                    max_value=24,
                    value=6,
                    key="loop_iterations"
                )
            
            with col_loop3:
                st.metric("Длительность", f"{(loop_interval * loop_iterations) // 60} мин")
            
            if st.button("🔄 ЗАПУСТИТЬ THE LOOP", use_container_width=True, key="start_loop"):
                with st.spinner(f"🔄 The Loop работает... (проверка каждые {loop_interval}с, {loop_iterations} итераций)"):
                    
                    # Progress tracking
                    loop_progress = st.progress(0)
                    loop_status = st.empty()
                    loop_log = st.empty()
                    
                    logs_text = []
                    
                    for i in range(1, loop_iterations + 1):
                        loop_progress.progress(i / loop_iterations)
                        loop_status.markdown(f"**🔄 Итерация {i}/{loop_iterations}**")
                        
                        # Check health
                        try:
                            import urllib.request
                            import json as json_module
                            
                            health = {
                                "timestamp": datetime.now().isoformat(),
                                "docker": "checking",
                                "http": "checking",
                                "overall": "checking"
                            }
                            
                            # Docker check
                            docker_result = subprocess.run(
                                ["docker", "ps", "-a", "--filter", "name=app", "--format", "{{.Status}}"],
                                capture_output=True, text=True, timeout=10
                            )
                            if "Up" in docker_result.stdout:
                                health["docker"] = "healthy"
                            elif "Exited" in docker_result.stdout:
                                health["docker"] = "crashed"
                            else:
                                health["docker"] = "not_found"
                            
                            # HTTP check
                            try:
                                with urllib.request.urlopen("http://localhost:8080", timeout=3) as r:
                                    health["http"] = "healthy" if r.getcode() == 200 else "degraded"
                            except:
                                health["http"] = "unreachable"
                            
                            # Determine overall
                            if health["docker"] == "healthy" and health["http"] == "healthy":
                                health["overall"] = "healthy"
                                log_entry = f"[{datetime.now().strftime('%H:%M:%S')}] ✅ HEALTHY - Docker: {health['docker']}, HTTP: {health['http']}"
                            elif health["docker"] == "crashed" or health["http"] == "unreachable":
                                health["overall"] = "critical"
                                log_entry = f"[{datetime.now().strftime('%H:%M:%S')}] 🔴 CRITICAL - Docker: {health['docker']}, HTTP: {health['http']}"
                                
                                # Attempt healing
                                logs_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] 💊 Attempting self-healing...")
                                try:
                                    subprocess.run(
                                        ["docker-compose", "restart"],
                                        cwd=os.path.join(latest["path"], "deploy"),
                                        capture_output=True, timeout=60
                                    )
                                    logs_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🐳 Container restarted")
                                except:
                                    logs_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Restart failed")
                            else:
                                health["overall"] = "degraded"
                                log_entry = f"[{datetime.now().strftime('%H:%M:%S')}] 🟡 DEGRADED - Docker: {health['docker']}, HTTP: {health['http']}"
                            
                            logs_text.append(log_entry)
                            
                            # Save status
                            status_file = os.path.join(latest["path"], "monitoring", "live_status.json")
                            os.makedirs(os.path.dirname(status_file), exist_ok=True)
                            with open(status_file, 'w', encoding='utf-8') as f:
                                json_module.dump(health, f, indent=2)
                            
                            # Update log display
                            loop_log.text_area("📜 Loop Log:", value="\n".join(logs_text[-10:]), height=150)
                            
                        except Exception as e:
                            logs_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Check failed: {str(e)[:50]}")
                            loop_log.text_area("📜 Loop Log:", value="\n".join(logs_text[-10:]), height=150)
                        
                        # Wait (but not after last iteration)
                        if i < loop_iterations:
                            time.sleep(loop_interval)
                    
                    loop_progress.progress(100)
                    st.success(f"✅ The Loop завершён после {loop_iterations} итераций")
            
            st.markdown("---")
            
            # ═══════════════════════════════════════════════════════════
            #                    📊 ОТЧЁТЫ И ЛОГИ
            # ═══════════════════════════════════════════════════════════
            
            col_reports, col_logs_area = st.columns(2)
            
            with col_reports:
                st.markdown("#### 📊 Health Report")
                health_file = os.path.join(latest["path"], "monitoring", "health_report.md")
                if health_content := read_file_safe(health_file):
                    st.markdown(health_content[:2000])
                else:
                    st.info("Отчет появится после запуска проекта")
                
                # Healing Log
                healing_log_file = os.path.join(latest["path"], "monitoring", "healing_log.json")
                if os.path.exists(healing_log_file):
                    with st.expander("📋 История исцелений"):
                        try:
                            import json
                            with open(healing_log_file, 'r') as f:
                                healing_log = json.load(f)
                            for entry in healing_log[-5:]:  # Последние 5
                                st.json(entry)
                        except:
                            st.error("Ошибка чтения лога")
            
            with col_logs_area:
                st.markdown("#### 📜 Логи самоисцеления")
                
                # Live logs text area
                logs_content = "[INFO] System monitoring active...\n"
                
                if live_status:
                    logs_content += f"[{live_status.get('timestamp', 'N/A')}] Status: {live_status.get('overall', 'unknown').upper()}\n"
                    if live_status.get("errors"):
                        for err in live_status["errors"]:
                            logs_content += f"[ERROR] {err}\n"
                    if live_status.get("actions_taken"):
                        for action in live_status["actions_taken"]:
                            logs_content += f"[ACTION] {action}\n"
                
                # Docker logs
                try:
                    result = subprocess.run(
                        ["docker", "logs", "--tail", "15", "app"],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.stdout or result.stderr:
                        logs_content += "\n--- Container Logs ---\n"
                        logs_content += (result.stdout + result.stderr)[-1000:]
                except:
                    logs_content += "\n[INFO] Docker logs unavailable"
                
                st.text_area("Live Logs:", value=logs_content, height=300)
            
            st.markdown("---")
            
            # Self-Healed Code
            healed_file = os.path.join(latest["path"], "source_code", "main_healed.py")
            if healed_content := read_file_safe(healed_file):
                with st.expander("💊 Self-Healed Code (v3)"):
                    st.code(healed_content, language="python")
        
        with tab8:
            readme_file = os.path.join(latest["path"], "README.md")
            if content := read_file_safe(readme_file):
                st.markdown(content)
            else:
                st.info("README не найден")
    else:
        st.info("📭 Нет созданных проектов")

st.markdown("---")

# Pipeline
st.markdown("### 🔄 Production Pipeline v10.0 (Self-Healing)")

pipeline_cols = st.columns(20)
pipeline_stages = ["👁️", "💰", "🔍", "🏗️", "🎨", "🔧", "👨‍💻", "📦", "🔍", "🔄", "✅", "🐳", "🐳", "📄", "⚙️", "📜", "📝", "🏥", "💊", "🌐"]
pipeline_names = ["Vision", "Budget", "Research", "Arch", "Diagram", "Stack", "Code", "Reqs", "QA1", "Fix", "QA2", "Docker", "Compose", ".env", "CI/CD", "Make", "README", "SRE", "Heal", "Deploy"]

for i, (col, icon, name) in enumerate(zip(pipeline_cols, pipeline_stages, pipeline_names)):
    with col:
        # Vision = green, DevOps = orange, SRE = red, Deploy = green
        if i == 0 or i == 19:
            color = "#11998e"  # Green
        elif i >= 17 and i <= 18:
            color = "#e74c3c"  # Red for SRE
        elif i >= 11 and i <= 16:
            color = "#f39c12"  # Orange for DevOps
        else:
            color = "#667eea"  # Purple for regular
        st.markdown(f"""
        <div style="text-align: center; padding: 0.2rem; background: linear-gradient(135deg, {color} 0%, #764ba2 100%); border-radius: 8px; margin: 1px;">
            <div style="font-size: 0.9rem;">{icon}</div>
            <div style="font-size: 0.4rem; color: white;">{name}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# История
st.markdown("### 📁 История проектов")

if projects:
    for project in projects[:5]:
        has_vision = os.path.exists(os.path.join(project["path"], "vision", "visual_analysis.md"))
        vision_badge = " 👁️" if has_vision else ""
        
        with st.expander(f"📂 {project['name']}{vision_badge} — {project['modified'].strftime('%d.%m.%Y %H:%M')}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(f"📂 Открыть", key=f"open_{project['name']}"):
                    if sys.platform == "win32":
                        os.startfile(project["path"])
            
            with col2:
                code_path = os.path.join(project["path"], "source_code", "main_fixed.py")
                if os.path.exists(code_path):
                    if st.button(f"▶️ Запустить", key=f"run_{project['name']}"):
                        result = subprocess.run(
                            [sys.executable, code_path],
                            capture_output=True, text=True, timeout=30
                        )
                        st.code(result.stdout if result.returncode == 0 else result.stderr)
            
            with col3:
                badges = []
                if os.path.exists(os.path.join(project["path"], "README.md")):
                    badges.append("📝")
                if os.path.exists(os.path.join(project["path"], "deploy", "Dockerfile")):
                    badges.append("🐳")
                if has_vision:
                    badges.append("👁️")
                st.markdown(" ".join(badges) if badges else "—")
else:
    st.info("📭 Пока нет проектов")

# Footer
st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: #888;">🧠 AI Software Factory v0.7 Nexus • Modular Architecture • ChromaDB Memory • The Loop • 2026</p>',
    unsafe_allow_html=True
)
