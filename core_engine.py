# ═══════════════════════════════════════════════════════════════
#            🧠 NEXUS v0.95 - THE NEXUS HIVE
#               SwarmMaster + Dynamic Expert Spawning
#         "Система сначала думает, кто ей нужен"
# ═══════════════════════════════════════════════════════════════

import os
import sys
import time
import json
import re
from typing import List, Dict, Any, Optional

# Windows encoding fix
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from crewai_tools import FileReadTool, SerperDevTool, ScrapeWebsiteTool, DirectoryReadTool
from dotenv import load_dotenv

load_dotenv(override=True)

# ═══════════════════════════════════════════════════════════════
#                    🤖 MODEL CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# v0.95 - The Nexus Hive Configuration
llm_boss = ChatOpenAI(model_name="gpt-4o", temperature=0.1)         # Strategic/Boss decisions
llm_specialist = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)  # Specialist work

# Aliases
llm_strategic = llm_boss
llm_worker = llm_specialist

# ═══════════════════════════════════════════════════════════════
#                    🛠️ TOOL CONFIGURATION
# ═══════════════════════════════════════════════════════════════

file_tool = FileReadTool()
search_tool = SerperDevTool()
web_tool = ScrapeWebsiteTool()
dir_tool = DirectoryReadTool()


# ═══════════════════════════════════════════════════════════════
#            🐝 SWARM MASTER - THE NEXUS HIVE v0.95
# ═══════════════════════════════════════════════════════════════

class SwarmMaster:
    """
    🧠 Ядро Системы v0.95: "The Nexus Hive"
    
    Система сначала "думает", какие эксперты ей нужны,
    затем динамически создает оптимальный рой агентов.
    """
    
    def __init__(self, goal: str):
        """
        Инициализация SwarmMaster.
        
        Args:
            goal: Описание мультизадачи
        """
        self.goal = goal
        self.workspace = f"./projects/{goal[:20].strip().replace(' ', '_')}"
        self.swarm_config: Dict[str, Any] = {}
        self.spawned_agents: List[Agent] = []
        self.all_tasks: List[Task] = []
        
        # Create workspace
        for folder in ['source_code', 'docs', 'deployment', 'tests', 'reports', 'swarm']:
            os.makedirs(f"{self.workspace}/{folder}", exist_ok=True)
        
        print(f"""
╔══════════════════════════════════════════════════════════════════╗
║            🧠 NEXUS v0.95 - THE NEXUS HIVE                       ║
╠══════════════════════════════════════════════════════════════════╣
║  📁 Workspace: {self.workspace:<48} ║
║  🎯 Goal: {goal[:50]:<53} ║
╚══════════════════════════════════════════════════════════════════╝
        """)

    def analyze_and_spawn(self) -> tuple:
        """
        Этап 1: Диспетчер анализирует задачу и нанимает экспертов.
        
        Returns:
            tuple: (workspace, result)
        """
        print(f"\n🚀 Swarm Manager анализирует задачу: {self.goal}\n")
        
        # Специальный агент-аналитик для декомпозиции
        dispatcher = Agent(
            role='Strategic Dispatcher',
            goal=f'Разбить задачу "{self.goal}" на подобласти и определить нужных экспертов.',
            backstory=f'''Ты — мозг системы v0.95. Ты решаешь, какие узкие специалисты нужны для победы.
            
            Доступные специализации:
            - Data Scientist / AI Engineer
            - UX/UI Designer
            - Security Expert / Penetration Tester
            - Backend Developer (Python, Go, Rust)
            - Frontend Developer (React, Vue, Angular)
            - DevOps Engineer (Docker, K8s, CI/CD)
            - Database Architect (SQL, NoSQL, Redis)
            - Mobile Developer (iOS, Android, Flutter)
            - Blockchain Developer (Solidity, Web3)
            - QA Automation Engineer
            - Technical Writer
            - System Architect
            
            Выбери 3-5 наиболее критичных ролей для задачи.
            
            ФОРМАТ ВЫВОДА (строго JSON):
            {{
                "complexity": "LOW|MEDIUM|HIGH|EXTREME",
                "experts": [
                    {{"role": "...", "goal": "...", "backstory": "..."}},
                    {{"role": "...", "goal": "...", "backstory": "..."}}
                ],
                "reasoning": "Почему выбраны эти эксперты"
            }}''',
            llm=llm_boss,
            verbose=True
        )

        analysis_task = Task(
            description=f'''Проанализируй мультизадачу: {self.goal}
            
            Выдели 3-5 критических ролей экспертов.
            
            Верни ТОЛЬКО JSON (без markdown):
            {{
                "complexity": "...",
                "experts": [
                    {{"role": "Data Scientist", "goal": "...", "backstory": "..."}},
                    ...
                ],
                "reasoning": "..."
            }}''',
            expected_output="JSON с полями: complexity, experts[], reasoning",
            agent=dispatcher,
            output_file=f"{self.workspace}/swarm/dispatch_analysis.json"
        )

        print("┌────────────────────────────────────────────────────────────────┐")
        print("│  🔍 PHASE 1: Strategic Dispatch Analysis                        │")
        print("└────────────────────────────────────────────────────────────────┘\n")

        # Магия: получаем структуру роя
        crew_analysis = Crew(
            agents=[dispatcher], 
            tasks=[analysis_task], 
            verbose=True
        )
        result = crew_analysis.kickoff(inputs={'topic': self.goal})
        
        # Парсим результат
        self._parse_swarm_config(str(result))
        
        # Строим и запускаем финальный рой
        return self.build_final_swarm()

    def _parse_swarm_config(self, result_text: str):
        """Парсит JSON-конфигурацию роя из результата анализа."""
        try:
            # Ищем JSON в тексте
            json_patterns = [
                r'\{[^{}]*"experts"\s*:\s*\[[^\]]*\][^{}]*\}',
                r'\{[^{}]*"complexity"[^{}]*"experts"[^{}]*\}',
            ]
            
            for pattern in json_patterns:
                match = re.search(pattern, result_text, re.DOTALL)
                if match:
                    self.swarm_config = json.loads(match.group())
                    break
            
            if not self.swarm_config:
                # Fallback: пробуем распарсить весь текст
                self.swarm_config = json.loads(result_text)
                
        except json.JSONDecodeError:
            print("⚠️ JSON parsing failed, using fallback config")
            self.swarm_config = {
                "complexity": "MEDIUM",
                "experts": [
                    {"role": "System Architect", "goal": f"Спроектировать архитектуру для {self.goal}", "backstory": "Эксперт по системному дизайну"},
                    {"role": "Lead Developer", "goal": f"Написать код для {self.goal}", "backstory": "Senior разработчик"},
                    {"role": "QA Engineer", "goal": "Протестировать и найти баги", "backstory": "Дотошный тестировщик"}
                ],
                "reasoning": "Базовый набор для любого проекта"
            }
        
        complexity = self.swarm_config.get('complexity', 'MEDIUM')
        experts = self.swarm_config.get('experts', [])
        
        print(f"""
┌────────────────────────────────────────────────────────────────┐
│  🐝 SWARM DISPATCH RESULT:                                     │
│     Complexity: {complexity:<46} │
│     Experts identified: {len(experts):<39} │
└────────────────────────────────────────────────────────────────┘
        """)
        
        # Save config
        with open(f"{self.workspace}/swarm/config.json", 'w', encoding='utf-8') as f:
            json.dump(self.swarm_config, f, indent=2, ensure_ascii=False)

    def _spawn_expert(self, expert_config: Dict[str, str]) -> Agent:
        """Создает агента-эксперта из конфигурации."""
        return Agent(
            role=expert_config.get('role', 'Expert'),
            goal=expert_config.get('goal', f'Решить подзадачу для {self.goal}'),
            backstory=f'''{expert_config.get('backstory', 'Элитный эксперт')}
            
            Ты был нанят Strategic Dispatcher для решения критической части проекта.
            ВАЖНО: Выводи ТОЛЬКО чистый код/контент БЕЗ markdown разметки!''',
            llm=llm_specialist,
            verbose=True
        )

    def _get_core_agents(self) -> Dict[str, Agent]:
        """Создает базовых агентов системы (всегда присутствуют)."""
        return {
            'architect': Agent(
                role='Nexus Architect',
                goal='Проектирование архитектуры и координация модулей.',
                backstory='Ты создаешь чертежи, которые выдержат любую нагрузку.',
                llm=llm_boss,
                verbose=True
            ),
            'coder': Agent(
                role='Lead Developer',
                goal='Написать чистый, рабочий код.',
                backstory='''Твой код — эталон PEP8 и безопасности.
                КРИТИЧНО: НИКОГДА не используй markdown (```) в выходных файлах!''',
                tools=[file_tool],
                llm=llm_boss,
                verbose=True
            ),
            'security': Agent(
                role='Security Auditor',
                goal='Защитить систему и внедрить Kill Switch.',
                backstory='Ты гарантируешь безопасность и протокол экстренной остановки.',
                tools=[file_tool],
                llm=llm_boss,
                verbose=True
            ),
            'sre': Agent(
                role='SRE Observer',
                goal='Настроить Docker и мониторинг.',
                backstory='Ты следишь за жизнью проекта после деплоя.',
                llm=llm_specialist,
                verbose=True
            )
        }

    def build_final_swarm(self) -> tuple:
        """
        Этап 2: Сборка финального роя и запуск производства.
        
        Returns:
            tuple: (workspace, result)
        """
        print("\n┌────────────────────────────────────────────────────────────────┐")
        print("│  🛠️ PHASE 2: Building Final Swarm                               │")
        print("└────────────────────────────────────────────────────────────────┘\n")
        
        # 1. Базовые агенты (всегда есть)
        core_agents = self._get_core_agents()
        
        # 2. Динамические эксперты из swarm_config
        experts = self.swarm_config.get('experts', [])
        for i, expert_config in enumerate(experts):
            expert_agent = self._spawn_expert(expert_config)
            self.spawned_agents.append(expert_agent)
            print(f"     🐝 Spawned: {expert_config.get('role', f'Expert {i+1}')}")
        
        # 3. Формируем полный список агентов
        all_agents = list(core_agents.values()) + self.spawned_agents
        
        print(f"\n     📊 Total agents in swarm: {len(all_agents)}")
        print(f"     🧠 Core agents: {len(core_agents)}")
        print(f"     🐝 Dynamic experts: {len(self.spawned_agents)}\n")
        
        # 4. Создаем задачи
        tasks = self._create_production_tasks(core_agents)
        
        # 5. Добавляем задачи для динамических экспертов
        for i, (expert_agent, expert_config) in enumerate(zip(self.spawned_agents, experts)):
            expert_task = Task(
                description=f'''Как {expert_config.get("role", "Expert")}, выполни свою часть для проекта: {self.goal}
                
                Твоя цель: {expert_config.get("goal", "Решить подзадачу")}
                
                Выведи результат своей работы (код, рекомендации, анализ).
                БЕЗ markdown разметки!''',
                expected_output=f"Результат работы {expert_config.get('role', 'Expert')}",
                agent=expert_agent,
                output_file=f"{self.workspace}/swarm/expert_{i+1}_{expert_config.get('role', 'expert').replace(' ', '_').lower()}.md"
            )
            tasks.insert(2 + i, expert_task)  # После архитектуры
        
        print("┌────────────────────────────────────────────────────────────────┐")
        print("│  🚀 PHASE 3: Production Launch                                  │")
        print(f"│     Agents: {len(all_agents):<51} │")
        print(f"│     Tasks: {len(tasks):<52} │")
        print("└────────────────────────────────────────────────────────────────┘\n")
        
        # 6. Запускаем Crew с иерархическим процессом
        final_crew = Crew(
            agents=all_agents,
            tasks=tasks,
            process=Process.hierarchical,
            manager_llm=llm_boss,
            memory=True,
            verbose=True
        )
        
        start_time = time.time()
        result = final_crew.kickoff(inputs={'topic': self.goal})
        elapsed = time.time() - start_time
        
        print(f"""
╔══════════════════════════════════════════════════════════════════╗
║            ✅ THE NEXUS HIVE v0.95 COMPLETE!                     ║
╠══════════════════════════════════════════════════════════════════╣
║  📁 Output: {self.workspace:<51} ║
║  ⏱️  Time: {elapsed:.1f}s                                          ║
║  🐝 Swarm size: {len(all_agents)} agents ({len(self.spawned_agents)} dynamic experts)             ║
║  📋 Tasks completed: {len(tasks):<42} ║
╚══════════════════════════════════════════════════════════════════╝
        """)
        
        return self.workspace, result

    def _create_production_tasks(self, core_agents: Dict[str, Agent]) -> List[Task]:
        """Создает базовые производственные задачи."""
        tasks = []
        
        # Architecture
        tasks.append(Task(
            description=f'''Спроектируй архитектуру для: {self.goal}
            
            Включи:
            1. Структуру модулей
            2. Потоки данных
            3. API контракты
            4. Mermaid диаграмму''',
            expected_output="Архитектурный документ.",
            agent=core_agents['architect'],
            output_file=f"{self.workspace}/docs/architecture.md"
        ))
        
        # Main Code
        tasks.append(Task(
            description=f'''Напиши main.py для: {self.goal}
            
            КРИТИЧНО:
            - БЕЗ markdown (```)!
            - Чистый Python код
            - Docstrings + type hints
            - Обработка ошибок''',
            expected_output="Python код.",
            agent=core_agents['coder'],
            output_file=f"{self.workspace}/source_code/main.py"
        ))
        
        # Requirements
        tasks.append(Task(
            description='Создай requirements.txt (БЕЗ markdown!). Формат: library==version',
            expected_output="requirements.txt",
            agent=core_agents['coder'],
            output_file=f"{self.workspace}/source_code/requirements.txt"
        ))
        
        # Security Module
        tasks.append(Task(
            description='''Создай security_control.py:
            1. Kill Switch (emergency_stop())
            2. Data Leak Detection
            3. Alert System
            БЕЗ markdown!''',
            expected_output="security_control.py",
            agent=core_agents['security'],
            output_file=f"{self.workspace}/source_code/security_control.py"
        ))
        
        # Security Audit
        tasks.append(Task(
            description='Security Audit. Вердикт: SECURE ✅ или VULNERABLE ❌',
            expected_output="Security report.",
            agent=core_agents['security'],
            output_file=f"{self.workspace}/reports/security_audit.md"
        ))
        
        # Dockerfile
        tasks.append(Task(
            description='''Создай Dockerfile (БЕЗ markdown!):
            - FROM python:3.11-slim
            - Non-root user
            - HEALTHCHECK''',
            expected_output="Dockerfile",
            agent=core_agents['sre'],
            output_file=f"{self.workspace}/deployment/Dockerfile"
        ))
        
        # Docker Compose
        tasks.append(Task(
            description='Создай docker-compose.yml (БЕЗ markdown!)',
            expected_output="docker-compose.yml",
            agent=core_agents['sre'],
            output_file=f"{self.workspace}/deployment/docker-compose.yml"
        ))
        
        return tasks


def run_nexus_hive(goal: str) -> tuple:
    """
    🚀 Точка входа для The Nexus Hive v0.95.
    
    Args:
        goal: Описание мультизадачи
        
    Returns:
        tuple: (workspace, result)
    """
    master = SwarmMaster(goal)
    return master.analyze_and_spawn()

# ═══════════════════════════════════════════════════════════════
#                🐝 SWARM INTELLIGENCE MODULE
# ═══════════════════════════════════════════════════════════════

# Каталог доступных специализаций
SPECIALIST_CATALOG = {
    'blockchain': 'Blockchain & Smart Contracts (Solidity, Web3.py, DeFi)',
    'ai_ml': 'AI/ML Engineering (PyTorch, TensorFlow, LangChain)',
    'bigdata': 'Big Data Processing (Spark, Hadoop, Kafka)',
    'uiux': 'UI/UX Design (Figma specs to code, CSS, React)',
    'database': 'Database Architecture (PostgreSQL, MongoDB, Redis)',
    'devops': 'Advanced DevOps (Kubernetes, Terraform, AWS/GCP)',
    'security': 'Penetration Testing (OWASP, Cryptography)',
    'mobile': 'Mobile Development (React Native, Flutter)',
    'game': 'Game Development (Pygame, Unity scripting)',
    'iot': 'IoT & Embedded (MQTT, Raspberry Pi, Arduino)',
    'fintech': 'Financial Engineering (Trading, Risk, Compliance)',
    'nlp': 'NLP Specialist (Transformers, spaCy, BERT)',
    'computer_vision': 'Computer Vision (OpenCV, YOLO, OCR)',
    'api': 'API Design (REST, GraphQL, gRPC)',
    'testing': 'QA Automation (Pytest, Selenium, Load Testing)'
}

def spawn_specialist(topic: str, expertise: str) -> Agent:
    """
    🐝 Динамическое создание узкого специалиста.
    
    Args:
        topic: Название проекта
        expertise: Ключ из SPECIALIST_CATALOG
        
    Returns:
        Agent: Специализированный агент
    """
    expertise_desc = SPECIALIST_CATALOG.get(expertise, expertise)
    
    return Agent(
        role=f'{expertise.title().replace("_", " ")} Specialist',
        goal=f'Решить специфическую подзадачу в области {expertise_desc} для проекта: {topic}',
        backstory=f'''Ты — лучший в мире эксперт по {expertise_desc}. 
        Тебя нанял Swarm Manager для ювелирной работы над критически важной частью проекта.
        
        Твоя экспертиза:
        - {expertise_desc}
        - Глубокое знание best practices
        - Опыт в production системах
        
        ВАЖНО: Выводи ТОЛЬКО чистый код без markdown!''',
        llm=llm_boss,
        verbose=True
    )


def create_swarm_manager() -> Agent:
    """Создает Swarm Manager - дирижера AI роя."""
    
    return Agent(
        role='Swarm Orchestrator',
        goal='Анализировать сложность мультизадачи и динамически формировать состав экспертных групп.',
        backstory=f'''Ты — дирижер искусственного интеллекта. Ты решаешь, сколько и каких специалистов нужно для идеального выполнения задачи.
        
        Доступные специализации:
        {json.dumps(SPECIALIST_CATALOG, indent=2, ensure_ascii=False)}
        
        Твои критерии принятия решений:
        1. Сложность технического стека
        2. Наличие нестандартных требований
        3. Междисциплинарность задачи
        4. Риски безопасности
        5. Необходимость специфической экспертизы
        
        Формат вывода (JSON):
        {{
            "complexity": "LOW|MEDIUM|HIGH|EXTREME",
            "required_specialists": ["specialist_key1", "specialist_key2"],
            "reasoning": "Почему нужны эти специалисты",
            "task_breakdown": ["подзадача1", "подзадача2"]
        }}''',
        llm=llm_strategic,
        verbose=True
    )


# ═══════════════════════════════════════════════════════════════
#            🧠 SWARM ENGINE CLASS (v1.1 Hierarchical)
# ═══════════════════════════════════════════════════════════════

class SwarmEngine:
    """
    🐝 Высшая нервная система NEXUS.
    
    Класс-ориентированная архитектура для управления динамическим роем агентов.
    Поддерживает иерархический процесс выполнения с центральным управлением.
    """
    
    def __init__(self, topic: str, enable_hierarchical: bool = True):
        """
        Инициализация движка роя.
        
        Args:
            topic: Описание проекта/задачи
            enable_hierarchical: Использовать Process.hierarchical (рекомендуется)
        """
        self.topic = topic
        self.enable_hierarchical = enable_hierarchical
        self.workspace = self._create_workspace()
        self.spawned_specialists: List[Agent] = []
        self.analysis_result: Dict[str, Any] = {}
        
    def _create_workspace(self) -> str:
        """Создает рабочую директорию проекта."""
        clean_name = "".join(c for c in self.topic if c.isalnum() or c in (' ', '_')).strip()
        clean_name = clean_name.replace(' ', '_')[:30]
        workspace = f"./projects/{clean_name}"
        
        folders = ['source_code', 'docs', 'deployment', 'tests', 'reports', 'swarm']
        for folder in folders:
            os.makedirs(f"{workspace}/{folder}", exist_ok=True)
        
        return workspace
    
    def get_core_agents(self) -> tuple:
        """
        Создает базовых агентов системы.
        
        Returns:
            tuple: (manager, architect, coder, qa, mentor, security, sre)
        """
        # 🐝 Диспетчер роя (Chief AI Officer)
        manager = Agent(
            role='Swarm Manager (Chief AI Officer)',
            goal=f'Проанализировать сложность задачи "{self.topic}" и сформировать оптимальный рой экспертов.',
            backstory=f'''Ты — мозг системы. Ты видишь проект целиком и понимаешь, какие узкие специалисты нужны для успеха.
            
            Доступные специализации:
            {json.dumps(SPECIALIST_CATALOG, indent=2, ensure_ascii=False)}
            
            Твои решения должны быть в формате JSON.''',
            llm=llm_strategic,
            verbose=True
        )
        
        # 🏗️ Архитектор системы
        architect = Agent(
            role='Nexus Architect',
            goal='Проектирование мульти-модульных систем и контроль целостности архитектуры.',
            backstory='Ты проектируешь связи между всеми агентами и модулями. Твои чертежи выдержат любую нагрузку.',
            llm=llm_strategic,
            verbose=True
        )
        
        # 👨‍💻 Lead Developer
        coder = Agent(
            role='Lead Developer',
            goal='Написать чистый код, Docker-конфиги и системные файлы.',
            backstory='''Твой код — эталон качества PEP8 и безопасности.
            КРИТИЧНО: НИКОГДА не используй markdown (```) в выходных файлах!''',
            tools=[file_tool],
            llm=llm_strategic,
            verbose=True
        )
        
        # 🧪 QA Engineer
        qa = Agent(
            role='QA Engineer',
            goal='Найти баги, запустить тесты и проверить работоспособность.',
            backstory='Ты — последний рубеж перед запуском. Ты беспощаден к ошибкам.',
            llm=llm_strategic,
            verbose=True
        )
        
        # 🎓 Performance Mentor
        mentor = Agent(
            role='Performance Mentor',
            goal='Оптимизировать код по KPI: скорость и использование памяти.',
            backstory='Ты делаешь код быстрым и легким, устраняя лишние вычисления.',
            llm=llm_strategic,
            verbose=True
        )
        
        # 🔐 Security Auditor
        security = Agent(
            role='Security Auditor',
            goal='Защитить систему от взлома и внедрить Kill Switch (UEP).',
            backstory='Ты гарантируешь безопасность и протокол экстренной остановки.',
            tools=[file_tool],
            llm=llm_strategic,
            verbose=True
        )
        
        # 🏥 SRE Observer
        sre = Agent(
            role='SRE Observer',
            goal='Настроить мониторинг и систему самозаживления.',
            backstory='Ты следишь за жизнью проекта после деплоя.',
            llm=llm_specialist,
            verbose=True
        )
        
        return manager, architect, coder, qa, mentor, security, sre
    
    def spawn_specialists(self, requirements: List[Dict[str, str]]) -> List[Agent]:
        """
        🐝 Динамическое создание агентов под специфику задачи.
        
        Args:
            requirements: Список требований от Swarm Manager
                         [{"role": "...", "goal": "...", "backstory": "..."}, ...]
        
        Returns:
            List[Agent]: Созданные специалисты
        """
        specialists = []
        
        for req in requirements:
            agent = Agent(
                role=f'Specialist: {req.get("role", "Expert")}',
                goal=req.get("goal", f'Решить подзадачу для {self.topic}'),
                backstory=f'''Ты — элитный эксперт, вызванный Swarm Manager.
                {req.get("backstory", "")}
                ВАЖНО: Выводи ТОЛЬКО чистый код без markdown!''',
                llm=llm_specialist,
                verbose=True
            )
            specialists.append(agent)
            
        self.spawned_specialists = specialists
        return specialists
    
    def spawn_from_catalog(self, expertise_keys: List[str]) -> List[Agent]:
        """
        🐝 Создание специалистов из каталога по ключам.
        
        Args:
            expertise_keys: Список ключей из SPECIALIST_CATALOG
            
        Returns:
            List[Agent]: Созданные специалисты
        """
        specialists = []
        
        for key in expertise_keys:
            if key in SPECIALIST_CATALOG:
                agent = spawn_specialist(self.topic, key)
                specialists.append(agent)
                print(f"     🐝 Spawned: {key.upper()} Specialist")
                
        self.spawned_specialists = specialists
        return specialists
    
    def analyze_task(self) -> Dict[str, Any]:
        """
        🔍 Первый проход: Swarm Manager анализирует задачу.
        
        Returns:
            dict: Результат анализа с complexity и required_specialists
        """
        manager, *_ = self.get_core_agents()
        
        analysis_task = Task(
            description=f'''Проведи глубокий анализ задачи: {self.topic}
            
            Определи:
            1. Уровень сложности (LOW / MEDIUM / HIGH / EXTREME)
            2. 3-5 ключевых ролей специалистов из каталога
            3. Обоснование выбора
            
            Каталог: {list(SPECIALIST_CATALOG.keys())}
            
            ВЕРНИ JSON:
            {{
                "complexity": "...",
                "required_specialists": ["key1", "key2"],
                "reasoning": "...",
                "task_breakdown": ["task1", "task2"]
            }}''',
            agent=manager,
            expected_output="JSON с анализом и списком специалистов.",
            output_file=f"{self.workspace}/swarm/analysis.json"
        )
        
        analysis_crew = Crew(
            agents=[manager],
            tasks=[analysis_task],
            process=Process.sequential,
            verbose=True
        )
        
        result = analysis_crew.kickoff(inputs={'topic': self.topic})
        
        # Парсим результат
        try:
            result_text = str(result)
            json_match = re.search(r'\{[^{}]*"complexity"[^{}]*\}', result_text, re.DOTALL)
            if json_match:
                self.analysis_result = json.loads(json_match.group())
        except Exception as e:
            print(f"⚠️ Analysis parsing error: {e}")
            self.analysis_result = {'complexity': 'MEDIUM', 'required_specialists': []}
        
        return self.analysis_result
    
    def create_production_tasks(self, agents: Dict[str, Agent]) -> List[Task]:
        """
        📋 Создает pipeline задач для производства.
        
        Args:
            agents: Словарь агентов
            
        Returns:
            List[Task]: Список задач
        """
        tasks = []
        
        # Research
        tasks.append(Task(
            description=f'Исследуй лучшие практики для: {self.topic}',
            expected_output="Технический отчет.",
            agent=agents.get('architect', agents['manager']),
            output_file=f"{self.workspace}/docs/research.md"
        ))
        
        # Architecture
        tasks.append(Task(
            description='Спроектируй архитектуру с Mermaid диаграммой.',
            expected_output="Архитектурный документ.",
            agent=agents['architect'],
            output_file=f"{self.workspace}/docs/architecture.md"
        ))
        
        # Coding
        tasks.append(Task(
            description=f'''Напиши main.py для: {self.topic}
            КРИТИЧНО: БЕЗ markdown! Чистый Python код.''',
            expected_output="Python код.",
            agent=agents['coder'],
            output_file=f"{self.workspace}/source_code/main.py"
        ))
        
        # Requirements
        tasks.append(Task(
            description='Создай requirements.txt (БЕЗ markdown!)',
            expected_output="requirements.txt",
            agent=agents['coder'],
            output_file=f"{self.workspace}/source_code/requirements.txt"
        ))
        
        # QA
        tasks.append(Task(
            description='Протестируй код. Вердикт: PASSED ✅ или FAILED ❌',
            expected_output="QA отчет.",
            agent=agents['qa'],
            output_file=f"{self.workspace}/tests/qa_report.md"
        ))
        
        # Performance
        tasks.append(Task(
            description='Аудит производительности. Оценка 1-10.',
            expected_output="Performance audit.",
            agent=agents['mentor'],
            output_file=f"{self.workspace}/docs/performance_audit.md"
        ))
        
        # Security
        tasks.append(Task(
            description='''Создай security_control.py:
            1. Kill Switch (emergency_stop)
            2. Data Leak Detection
            3. Alert System
            БЕЗ markdown!''',
            expected_output="security_control.py",
            agent=agents['security'],
            output_file=f"{self.workspace}/source_code/security_control.py"
        ))
        
        # Security Audit
        tasks.append(Task(
            description='Security Audit. Вердикт: SECURE ✅ или VULNERABLE ❌',
            expected_output="Security report.",
            agent=agents['security'],
            output_file=f"{self.workspace}/reports/security_audit.md"
        ))
        
        # Dockerfile
        tasks.append(Task(
            description='Создай Dockerfile (БЕЗ markdown!)',
            expected_output="Dockerfile",
            agent=agents['sre'],
            output_file=f"{self.workspace}/deployment/Dockerfile"
        ))
        
        # Docker Compose
        tasks.append(Task(
            description='Создай docker-compose.yml (БЕЗ markdown!)',
            expected_output="docker-compose.yml",
            agent=agents['sre'],
            output_file=f"{self.workspace}/deployment/docker-compose.yml"
        ))
        
        return tasks
    
    def run(self) -> tuple:
        """
        🚀 Основной метод запуска SwarmEngine.
        
        Returns:
            tuple: (workspace, result)
        """
        print(f"""
╔══════════════════════════════════════════════════════════════════╗
║           🧠 NEXUS v1.1 - SwarmEngine HIERARCHICAL               ║
╠══════════════════════════════════════════════════════════════════╣
║  📁 Workspace: {self.workspace:<48} ║
║  🎯 Goal: {self.topic[:50]:<53} ║
║  🔄 Process: {'HIERARCHICAL' if self.enable_hierarchical else 'SEQUENTIAL':<45} ║
╚══════════════════════════════════════════════════════════════════╝
        """)
        
        # Phase 1: Анализ роя
        print("\n🐝 PHASE 1: Swarm Analysis...")
        analysis = self.analyze_task()
        
        complexity = analysis.get('complexity', 'MEDIUM')
        required_specialists = analysis.get('required_specialists', [])
        
        print(f"""
┌────────────────────────────────────────────────────────────────────┐
│  🐝 SWARM DECISION:                                                │
│     Complexity: {complexity:<48} │
│     Specialists: {len(required_specialists):<47} │
└────────────────────────────────────────────────────────────────────┘
        """)
        
        # Phase 2: Spawn specialists
        print("\n🐝 PHASE 2: Spawning Specialists...")
        specialists = self.spawn_from_catalog(required_specialists)
        
        # Phase 3: Assemble core agents
        manager, architect, coder, qa, mentor, security, sre = self.get_core_agents()
        
        agents_dict = {
            'manager': manager,
            'architect': architect,
            'coder': coder,
            'qa': qa,
            'mentor': mentor,
            'security': security,
            'sre': sre
        }
        
        # Phase 4: Create tasks
        tasks = self.create_production_tasks(agents_dict)
        
        # Add specialist tasks
        for i, specialist in enumerate(specialists):
            expertise = required_specialists[i] if i < len(required_specialists) else f"specialist_{i}"
            specialist_task = Task(
                description=f'Экспертная задача для {specialist.role}: {self.topic}',
                expected_output=f"Экспертный отчет по {expertise}.",
                agent=specialist,
                output_file=f"{self.workspace}/swarm/{expertise}_report.md"
            )
            tasks.insert(2 + i, specialist_task)  # Insert after architecture
        
        # Phase 5: Assemble and run crew
        all_agents = [manager, architect, coder, qa, mentor, security, sre] + specialists
        
        print(f"\n🚀 PHASE 5: Running Crew ({len(all_agents)} agents, {len(tasks)} tasks)...")
        
        if self.enable_hierarchical:
            # Иерархический процесс с manager как ведущим
            crew = Crew(
                agents=all_agents,
                tasks=tasks,
                process=Process.hierarchical,
                manager_llm=llm_strategic,
                memory=True,
                verbose=True
            )
        else:
            # Последовательный процесс (fallback)
            crew = Crew(
                agents=all_agents,
                tasks=tasks,
                process=Process.sequential,
                memory=True,
                verbose=True
            )
        
        start_time = time.time()
        result = crew.kickoff(inputs={'topic': self.topic})
        elapsed = time.time() - start_time
        
        print(f"""
╔══════════════════════════════════════════════════════════════════╗
║               ✅ SWARM ENGINE v1.1 COMPLETE!                     ║
╠══════════════════════════════════════════════════════════════════╣
║  📁 Output: {self.workspace:<51} ║
║  ⏱️  Time: {elapsed:.1f}s                                          ║
║  🐝 Agents: {len(all_agents)} ({len(specialists)} specialists)                       ║
║  📋 Tasks: {len(tasks):<52} ║
║  🔄 Process: {'HIERARCHICAL' if self.enable_hierarchical else 'SEQUENTIAL':<45} ║
╚══════════════════════════════════════════════════════════════════╝
        """)
        
        return self.workspace, result


def start_swarm_production(goal: str, hierarchical: bool = True) -> tuple:
    """
    🚀 Точка входа для SwarmEngine.
    
    Args:
        goal: Описание проекта
        hierarchical: Использовать иерархический процесс
        
    Returns:
        tuple: (workspace, result)
    """
    engine = SwarmEngine(goal, enable_hierarchical=hierarchical)
    return engine.run()


# ═══════════════════════════════════════════════════════════════
#                    👥 CORE AGENT TEAM (7+1)
# ═══════════════════════════════════════════════════════════════

def create_agents():
    """Create the 8-agent Nexus team for v1.0 (7 core + Swarm Manager)"""
    
    # 🐝 SWARM MANAGER - Creates and orchestrates the swarm
    swarm_manager = create_swarm_manager()
    
    researcher = Agent(
        role='Global Tech Scout',
        goal='Найти самые эффективные библиотеки и API для {topic}',
        backstory='Ты аналитик, который знает все тренды разработки 2026 года.',
        tools=[search_tool],
        llm=llm_worker,
        verbose=True
    )

    architect = Agent(
        role='System Architect',
        goal='Спроектировать масштабируемую структуру проекта.',
        backstory='Ты создаешь чертежи, которые выдержат любую нагрузку.',
        llm=llm_boss,
        verbose=True
    )

    coder = Agent(
        role='Lead Developer',
        goal='Написать чистый код, Docker-конфиги и системные файлы.',
        backstory='''Твой код — эталон качества PEP8 и безопасности.
        
        КРИТИЧНО:
        - НИКОГДА не используй markdown (```) в выходных файлах
        - Пиши ТОЛЬКО чистый Python/YAML/Dockerfile
        - Начинай Python файлы с import или #
        - Добавляй docstrings к функциям''',
        tools=[file_tool],
        llm=llm_boss,
        verbose=True
    )

    qa = Agent(
        role='QA Engineer',
        goal='Найти баги, запустить тесты и проверить работоспособность.',
        backstory='Ты — последний рубеж перед запуском. Ты беспощаден к ошибкам.',
        llm=llm_boss,
        verbose=True
    )

    mentor = Agent(
        role='Performance Mentor',
        goal='Оптимизировать код по KPI: скорость и использование памяти.',
        backstory='''Ты делаешь код быстрым и легким, устраняя лишние вычисления.
        
        Оценивай по критериям:
        - 🏎️ Производительность (Big O)
        - 🧹 Чистота (PEP8)
        - 🔒 Безопасность
        - 📦 Модульность
        - 📝 Документация
        
        Выставляй оценку 1-10.''',
        llm=llm_boss,
        verbose=True
    )

    security = Agent(
        role='Security Auditor',
        goal='Защитить систему от взлома и внедрить Kill Switch (UEP).',
        backstory='''Ты гарантируешь, что софт безопасен и имеет протокол экстренной остановки.
        
        Твои задачи:
        - 🛑 Kill Switch — механизм мгновенной остановки
        - 🔍 Data Leak Detection — проверка на утечку данных
        - 🚨 Alert System — уведомления о критических сбоях
        - 🔐 Security Best Practices — OWASP, хеширование, шифрование
        
        КРИТИЧНО: Выводи ТОЛЬКО чистый Python код БЕЗ markdown!''',
        tools=[file_tool],
        llm=llm_boss,
        verbose=True
    )

    sre = Agent(
        role='SRE Observer',
        goal='Настроить мониторинг и систему самозаживления.',
        backstory='''Ты следишь за жизнью проекта после его деплоя.
        
        ВАЖНО: Выводи ТОЛЬКО чистые конфиги (YAML, Dockerfile) БЕЗ markdown!''',
        llm=llm_worker,
        verbose=True
    )
    
    return {
        'swarm_manager': swarm_manager,  # 🐝 Orchestrator
        'researcher': researcher,
        'architect': architect,
        'coder': coder,
        'qa': qa,
        'mentor': mentor,
        'security': security,
        'sre': sre
    }

# ═══════════════════════════════════════════════════════════════
#                    🚀 NEXUS KICKOFF v1.0 SWARM
# ═══════════════════════════════════════════════════════════════

def analyze_and_spawn_swarm(user_goal: str, agents: dict) -> tuple:
    """
    🐝 Phase 0: Swarm Manager анализирует задачу и создает специалистов.
    
    Returns:
        tuple: (spawned_specialists, swarm_analysis)
    """
    print("""
┌────────────────────────────────────────────────────────────────────┐
│  🐝 SWARM ANALYSIS PHASE                                           │
│     Swarm Manager анализирует сложность задачи...                  │
└────────────────────────────────────────────────────────────────────┘
    """)
    
    # Задача декомпозиции для Swarm Manager
    task_decomposition = Task(
        description=f'''Проанализируй мультизадачу: {user_goal}
        
        Определи:
        1. Уровень сложности (LOW / MEDIUM / HIGH / EXTREME)
        2. Нужны ли дополнительные узкие специалисты?
        
        Доступные специализации:
        - blockchain: Smart Contracts, Web3
        - ai_ml: Machine Learning, Neural Networks
        - bigdata: Spark, Kafka, Data Pipelines
        - uiux: Frontend Design, CSS
        - database: PostgreSQL, MongoDB, Redis
        - devops: Kubernetes, Terraform, Cloud
        - mobile: React Native, Flutter
        - fintech: Trading, Risk Management
        - nlp: NLP, Transformers
        - computer_vision: OpenCV, YOLO
        - api: REST, GraphQL, gRPC
        - testing: QA Automation, Load Testing
        
        ВЕРНИ JSON:
        {{
            "complexity": "LOW|MEDIUM|HIGH|EXTREME",
            "required_specialists": ["key1", "key2"],
            "reasoning": "Обоснование"
        }}''',
        expected_output="JSON с анализом сложности и списком специалистов.",
        agent=agents['swarm_manager']
    )
    
    # Мини-crew для анализа
    analysis_crew = Crew(
        agents=[agents['swarm_manager']],
        tasks=[task_decomposition],
        process=Process.sequential,
        verbose=True
    )
    
    analysis_result = analysis_crew.kickoff(inputs={'topic': user_goal})
    
    # Парсим результат
    spawned_specialists = []
    try:
        # Пытаемся извлечь JSON из результата
        result_text = str(analysis_result)
        json_match = re.search(r'\{[^{}]*"complexity"[^{}]*\}', result_text, re.DOTALL)
        
        if json_match:
            swarm_data = json.loads(json_match.group())
            required = swarm_data.get('required_specialists', [])
            
            print(f"""
┌────────────────────────────────────────────────────────────────────┐
│  🐝 SWARM DECISION:                                                │
│     Complexity: {swarm_data.get('complexity', 'MEDIUM'):<48} │
│     Specialists needed: {len(required):<41} │
└────────────────────────────────────────────────────────────────────┘
            """)
            
            # Создаем специалистов
            for expertise in required:
                if expertise in SPECIALIST_CATALOG:
                    specialist = spawn_specialist(user_goal, expertise)
                    spawned_specialists.append((expertise, specialist))
                    print(f"     🐝 Spawned: {expertise.upper()} Specialist")
            
            return spawned_specialists, swarm_data
    except Exception as e:
        print(f"     ⚠️ Swarm analysis fallback: {e}")
    
    return [], {'complexity': 'MEDIUM', 'required_specialists': []}


def run_ai_factory(user_goal, image_path=None, enable_swarm=True):
    """
    🚀 Запускает Nexus v1.0 SWARM Edition.
    
    Pipeline:
    [Swarm Analysis] → Researcher → Architect → [Specialists] → Coder → QA → Mentor → Security → SRE
    
    Args:
        user_goal: Description of the project to create
        image_path: Optional path to reference image
        enable_swarm: Enable dynamic specialist spawning (default True)
        
    Returns:
        tuple: (workspace_path, result)
    """
    
    # Create workspace
    clean_name = "".join(c for c in user_goal if c.isalnum() or c in (' ', '_')).strip()
    clean_name = clean_name.replace(' ', '_')[:30]
    workspace = f"./projects/{clean_name}"
    
    # Create all necessary directories
    for folder in ['source_code', 'docs', 'deployment', 'tests', 'reports', 'swarm']:
        os.makedirs(f"{workspace}/{folder}", exist_ok=True)

    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║           🧠 NEXUS v1.0 - AI Factory SWARM Edition               ║
╠══════════════════════════════════════════════════════════════════╣
║  📁 Workspace: {workspace:<48} ║
║  🎯 Goal: {user_goal[:50]:<53} ║
║                                                                  ║
║  👥 CORE AGENTS (8):                                             ║
║     🐝 Swarm Manager   → Orchestrate specialists 🆕              ║
║     🔍 Tech Scout      → Research best practices                 ║
║     🏗️  Architect       → Design architecture                    ║
║     👨‍💻 Lead Developer  → Write code + Docker                    ║
║     🧪 QA Engineer     → Test and validate                      ║
║     🎓 Perf. Mentor    → KPI optimization                       ║
║     🔐 Security Auditor → Kill Switch + Audit                   ║
║     🏥 SRE Observer    → Deploy + Monitor                       ║
║                                                                  ║
║  🐝 SWARM MODE: {'ENABLED' if enable_swarm else 'DISABLED':<47} ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    # Create core agents
    agents = create_agents()
    
    # 🐝 SWARM PHASE: Analyze and spawn specialists
    spawned_specialists = []
    swarm_analysis = {}
    
    if enable_swarm:
        spawned_specialists, swarm_analysis = analyze_and_spawn_swarm(user_goal, agents)
        
        # Save swarm analysis
        with open(f"{workspace}/swarm/analysis.json", 'w', encoding='utf-8') as f:
            json.dump(swarm_analysis, f, indent=2, ensure_ascii=False)

    # ═══════════════════════════════════════════════════════════
    #                    📋 TASK PIPELINE v1.0
    # ═══════════════════════════════════════════════════════════

    all_tasks = []
    all_agents = list(agents.values())
    
    # Add spawned specialists to agent pool
    for expertise, specialist in spawned_specialists:
        all_agents.append(specialist)

    # 1️⃣ Research
    task_research = Task(
        description=f'''Исследуй лучшие практики для: {user_goal}
        
        Найди:
        1. Актуальные библиотеки 2026 года
        2. Архитектурные паттерны
        3. Примеры реализации
        4. Потенциальные проблемы и риски''',
        expected_output="Технический отчет с рекомендациями.",
        agent=agents['researcher'],
        output_file=f"{workspace}/docs/research.md"
    )
    all_tasks.append(task_research)

    # 2️⃣ Architecture
    task_arch = Task(
        description='''Спроектируй масштабируемую архитектуру.
        
        Включи:
        1. Структуру модулей и классов
        2. Потоки данных
        3. Mermaid диаграмму
        4. API контракты''',
        expected_output="Архитектурный документ с Mermaid схемой.",
        agent=agents['architect'],
        context=[task_research],
        output_file=f"{workspace}/docs/architecture.md"
    )
    all_tasks.append(task_arch)
    
    # 🐝 SPECIALIST TASKS (if spawned)
    specialist_tasks = []
    for i, (expertise, specialist) in enumerate(spawned_specialists):
        specialist_task = Task(
            description=f'''Как эксперт по {SPECIALIST_CATALOG.get(expertise, expertise)}, 
            реши специфическую подзадачу для проекта: {user_goal}
            
            Твоя экспертиза критична для успеха проекта.
            
            Выведи:
            1. Рекомендации по {expertise}
            2. Код/конфиги если нужно (БЕЗ markdown!)
            3. Потенциальные проблемы и решения''',
            expected_output=f"Экспертный отчет по {expertise}.",
            agent=specialist,
            context=[task_arch],
            output_file=f"{workspace}/swarm/{expertise}_report.md"
        )
        specialist_tasks.append(specialist_task)
        all_tasks.append(specialist_task)
    
    if spawned_specialists:
        print(f"""
┌────────────────────────────────────────────────────────────────────┐
│  🐝 SWARM SPECIALISTS ACTIVATED: {len(spawned_specialists):<33} │
│     Tasks added to pipeline                                        │
└────────────────────────────────────────────────────────────────────┘
        """)

    # 3️⃣ Coding (now with specialist context)
    coding_context = [task_arch] + specialist_tasks if specialist_tasks else [task_arch]
    
    task_coding = Task(
        description=f'''Реализуй проект: {user_goal}
        
        Создай main.py с:
        1. Чистым Python кодом (БЕЗ markdown ```)
        2. Docstrings для всех функций
        3. Type hints
        4. Логирование
        5. Обработка ошибок
        
        {'Учти рекомендации специалистов из swarm!' if specialist_tasks else ''}
        
        КРИТИЧНО: НЕ используй markdown!''',
        expected_output="Готовый Python код.",
        agent=agents['coder'],
        context=coding_context,
        output_file=f"{workspace}/source_code/main.py"
    )
    all_tasks.append(task_coding)
    
    # 4️⃣ Requirements
    task_requirements = Task(
        description='''Создай requirements.txt (БЕЗ markdown!).
        Формат: library==version''',
        expected_output="requirements.txt",
        agent=agents['coder'],
        context=[task_coding],
        output_file=f"{workspace}/source_code/requirements.txt"
    )
    all_tasks.append(task_requirements)

    # 5️⃣ QA Testing
    task_qa = Task(
        description=f'''Проведи тесты кода.
        
        1. Проверь синтаксис
        2. Проанализируй логику
        3. Найди edge cases
        
        Вердикт: PASSED ✅ или FAILED ❌''',
        expected_output="QA отчет с вердиктом.",
        agent=agents['qa'],
        context=[task_coding],
        output_file=f"{workspace}/tests/qa_report.md"
    )
    all_tasks.append(task_qa)

    # 6️⃣ Performance Audit
    task_performance = Task(
        description='''Аудит производительности (KPI).
        
        Оцени по шкале 1-10:
        - 🏎️ Big O: __/10
        - 🧹 PEP8: __/10
        - 🔒 Security: __/10
        - 📦 Modularity: __/10
        - 📝 Docs: __/10
        
        ОБЩИЙ БАЛЛ: __/10
        ТОП-3 улучшения.''',
        expected_output="Performance audit.",
        agent=agents['mentor'],
        context=[task_coding, task_qa],
        output_file=f"{workspace}/docs/performance_audit.md"
    )
    all_tasks.append(task_performance)

    # 7️⃣ Security Module
    task_security = Task(
        description=f'''Создай security_control.py с:
        
        1. 🛑 KILL SWITCH:
           - emergency_stop()
           - SYSTEM_ACTIVE flag
           - Graceful shutdown
        
        2. 🔍 DATA LEAK DETECTION:
           - check_credentials()
           - mask_sensitive_data()
        
        3. 🚨 ALERT SYSTEM:
           - send_alert(severity, message)
           - Уровни: INFO, WARNING, CRITICAL
        
        КРИТИЧНО: ТОЛЬКО чистый Python, БЕЗ markdown!''',
        expected_output="security_control.py",
        agent=agents['security'],
        context=[task_coding],
        output_file=f"{workspace}/source_code/security_control.py"
    )
    all_tasks.append(task_security)
    
    # 8️⃣ Security Report
    task_security_report = Task(
        description='''Аудит безопасности проекта.
        
        Проверь:
        - Hardcoded secrets
        - SQL injection
        - XSS vulnerabilities
        - Rate limiting
        
        Вердикт: SECURE ✅ или VULNERABLE ❌''',
        expected_output="Security audit report.",
        agent=agents['security'],
        context=[task_coding, task_security],
        output_file=f"{workspace}/reports/security_audit.md"
    )
    all_tasks.append(task_security_report)

    # 9️⃣ Dockerfile
    task_dockerfile = Task(
        description='''Создай Dockerfile (БЕЗ markdown!).
        
        - FROM python:3.11-slim
        - Non-root user
        - HEALTHCHECK''',
        expected_output="Dockerfile",
        agent=agents['sre'],
        context=[task_coding, task_requirements],
        output_file=f"{workspace}/deployment/Dockerfile"
    )
    all_tasks.append(task_dockerfile)

    # 🔟 Docker Compose
    task_compose = Task(
        description='''Создай docker-compose.yml (БЕЗ markdown!).
        
        - version: '3.8'
        - healthcheck
        - restart policy''',
        expected_output="docker-compose.yml",
        agent=agents['sre'],
        context=[task_dockerfile],
        output_file=f"{workspace}/deployment/docker-compose.yml"
    )
    all_tasks.append(task_compose)

    # ═══════════════════════════════════════════════════════════
    #                    🚀 SWARM CREW EXECUTION
    # ═══════════════════════════════════════════════════════════
    
    total_agents = len(all_agents)
    total_tasks = len(all_tasks)
    
    print(f"""
┌────────────────────────────────────────────────────────────────────┐
│  🚀 EXECUTING SWARM CREW                                           │
│     Total Agents: {total_agents:<47} │
│     Total Tasks:  {total_tasks:<47} │
│     Specialists:  {len(spawned_specialists):<47} │
└────────────────────────────────────────────────────────────────────┘
    """)

    nexus_crew = Crew(
        agents=all_agents,
        tasks=all_tasks,
        process=Process.sequential,
        memory=True,
        verbose=True
    )

    start_time = time.time()
    result = nexus_crew.kickoff(inputs={'topic': user_goal})
    elapsed = time.time() - start_time
    
    # Generate swarm summary
    specialist_files = '\n'.join([f"║     swarm/{exp}_report.md" + " " * (32 - len(exp)) + f"— {exp.upper()} Expert       ║"
                                  for exp, _ in spawned_specialists]) if spawned_specialists else ""

    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║               ✅ NEXUS v1.0 SWARM COMPLETE!                      ║
╠══════════════════════════════════════════════════════════════════╣
║  📁 Output: {workspace:<51} ║
║  ⏱️  Time: {elapsed:.1f}s                                          ║
║  🐝 Swarm Size: {total_agents} agents ({len(spawned_specialists)} specialists)                       ║
║                                                                  ║
║  📄 Generated Files ({total_tasks}+):                                       ║
║     docs/research.md            — Tech research                  ║
║     docs/architecture.md        — Architecture + Mermaid         ║
║     docs/performance_audit.md   — KPI score 🎓                   ║
║     source_code/main.py         — Application code               ║
║     source_code/requirements.txt — Dependencies                  ║
║     source_code/security_control.py — 🔐 Kill Switch + Alerts   ║
║     tests/qa_report.md          — QA results                     ║
║     reports/security_audit.md   — 🔐 Security Audit              ║
║     deployment/Dockerfile       — Docker image                   ║
║     deployment/docker-compose.yml — Deploy config                ║
║     swarm/analysis.json         — 🐝 Swarm Analysis              ║
{specialist_files}
╚══════════════════════════════════════════════════════════════════╝
    """)

    return workspace, result


# ═══════════════════════════════════════════════════════════════
#                    🔧 UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def setup_workspace(project_name):
    """Create project workspace structure."""
    clean_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '_')).strip()
    clean_name = clean_name.replace(' ', '_')[:30]
    workspace = f"./projects/{clean_name}"
    
    folders = ['source_code', 'docs', 'deployment', 'tests', 'reports']
    for folder in folders:
        os.makedirs(f"{workspace}/{folder}", exist_ok=True)
    
    return workspace


def strip_markdown_from_code(code_content):
    """Remove markdown code blocks from generated code."""
    lines = code_content.split('\n')
    clean_lines = []
    in_code_block = False
    
    for line in lines:
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            continue
        if not line.strip().startswith('```'):
            clean_lines.append(line)
    
    return '\n'.join(clean_lines)


# Alias for backwards compatibility
start_production = run_ai_factory


# ═══════════════════════════════════════════════════════════════
#                    🐝 QUICK SWARM SPAWN
# ═══════════════════════════════════════════════════════════════

def quick_spawn_team(topic: str, specializations: list) -> list:
    """
    Быстрое создание команды специалистов без полного анализа.
    
    Args:
        topic: Проект
        specializations: Список ключей из SPECIALIST_CATALOG
        
    Returns:
        list: Список созданных агентов
    """
    team = []
    for spec in specializations:
        if spec in SPECIALIST_CATALOG:
            agent = spawn_specialist(topic, spec)
            team.append(agent)
            print(f"🐝 Spawned: {spec.upper()} Specialist")
    return team


def list_specialists():
    """Показать все доступные специализации."""
    print("\n🐝 AVAILABLE SPECIALISTS:\n")
    for key, desc in SPECIALIST_CATALOG.items():
        print(f"  • {key:<20} — {desc}")
    print()


# ═══════════════════════════════════════════════════════════════
#                    🚀 MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║           🧠 NEXUS v1.0 - AI Factory SWARM Edition               ║
║    8 Core Agents • Dynamic Specialists • Swarm Intelligence      ║
╠══════════════════════════════════════════════════════════════════╣
║  🐝 SWARM MODE: Автоматический анализ и создание специалистов    ║
║                                                                  ║
║  Available specialists: blockchain, ai_ml, bigdata, uiux,        ║
║  database, devops, mobile, fintech, nlp, computer_vision,        ║
║  api, testing, security, game, iot                               ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    if sys.stdin.isatty():
        user_goal = input("🎯 Что создаём? ").strip()
        
        if user_goal:
            # Ask about swarm mode
            swarm_mode = input("🐝 Включить Swarm Mode? (y/n, default=y): ").strip().lower()
            enable_swarm = swarm_mode != 'n'
            
            workspace, result = run_ai_factory(user_goal, enable_swarm=enable_swarm)
            print(f"\n📁 Проект готов: {workspace}")
        else:
            print("❌ Цель не указана")
    else:
        print("Running in non-interactive mode. Use run_ai_factory() directly.")
