import { useState, useEffect, useRef } from 'react'

// 🔧 НАСТРОЙКА API URL
// Production: Railway backend
// Development: localhost
const API_URL = import.meta.env.VITE_API_URL || 
  (import.meta.env.PROD 
    ? 'https://web-production-4f4fb.up.railway.app' 
    : 'http://127.0.0.1:8000')

// Компонент переключателя темы
const ThemeToggle = ({ isDark, onToggle }) => (
  <button
    onClick={onToggle}
    className={`
      relative w-16 h-8 rounded-full transition-all duration-300
      ${isDark 
        ? 'bg-slate-700 border border-slate-600' 
        : 'bg-amber-100 border border-amber-200'}
    `}
  >
    <div className={`
      absolute top-1 w-6 h-6 rounded-full transition-all duration-300 flex items-center justify-center
      ${isDark 
        ? 'left-1 bg-indigo-500' 
        : 'left-8 bg-amber-400'}
    `}>
      {isDark ? (
        <span className="text-xs">🌙</span>
      ) : (
        <span className="text-xs">☀️</span>
      )}
    </div>
  </button>
)

// Компонент карточки агента
const AgentCard = ({ name, role, status, active, icon, isDark }) => (
  <div className={`
    p-5 rounded-2xl border transition-all duration-500
    ${active 
      ? isDark 
        ? 'border-indigo-500/50 bg-indigo-950/40 shadow-[0_0_30px_rgba(99,102,241,0.2)] scale-[1.02]' 
        : 'border-indigo-400 bg-indigo-50 shadow-[0_0_30px_rgba(99,102,241,0.15)] scale-[1.02]'
      : isDark 
        ? 'border-slate-800/50 bg-slate-900/40 hover:border-slate-700'
        : 'border-slate-200 bg-white hover:border-slate-300 shadow-sm'}
    backdrop-blur-xl
  `}>
    <div className="flex justify-between items-start mb-3">
      <div className="text-2xl">{icon}</div>
      <div className={`
        w-3 h-3 rounded-full transition-all duration-300
        ${active 
          ? 'bg-indigo-500 animate-pulse shadow-[0_0_10px_rgba(99,102,241,0.8)]' 
          : isDark ? 'bg-slate-700' : 'bg-slate-300'}
      `} />
    </div>
    <h3 className={`font-medium text-lg tracking-wide ${isDark ? 'text-white' : 'text-slate-800'}`}>
      {name}
    </h3>
    <p className={`text-xs mt-1 uppercase tracking-wider ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
      {role}
    </p>
    <div className={`mt-4 pt-3 border-t ${isDark ? 'border-slate-800/50' : 'border-slate-100'}`}>
      <p className={`text-sm ${active ? 'text-indigo-500' : isDark ? 'text-slate-600' : 'text-slate-400'}`}>
        {status}
      </p>
    </div>
  </div>
)

// Компонент терминала
const Terminal = ({ logs, isDark }) => {
  const terminalRef = useRef(null)
  
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [logs])

  return (
    <div className={`
      rounded-2xl overflow-hidden backdrop-blur-xl border
      ${isDark 
        ? 'bg-slate-900/60 border-slate-800/50' 
        : 'bg-slate-50 border-slate-200 shadow-sm'}
    `}>
      {/* Заголовок терминала */}
      <div className={`
        flex items-center gap-2 px-4 py-3 border-b
        ${isDark ? 'border-slate-800/50' : 'border-slate-200'}
      `}>
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-500/80" />
          <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
          <div className="w-3 h-3 rounded-full bg-green-500/80" />
        </div>
        <span className={`text-xs ml-2 uppercase tracking-widest ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
          Singularity Terminal
        </span>
      </div>
      
      {/* Содержимое */}
      <div 
        ref={terminalRef}
        className={`p-4 font-mono text-sm h-64 overflow-y-auto ${isDark ? '' : 'bg-slate-900'}`}
      >
        {logs.map((log, i) => (
          <div key={i} className={`mb-1 ${
            log.type === 'success' ? 'text-emerald-400' :
            log.type === 'error' ? 'text-red-400' :
            log.type === 'info' ? 'text-indigo-400' :
            'text-slate-400'
          }`}>
            <span className="text-slate-600 mr-2">{log.time}</span>
            {log.message}
          </div>
        ))}
        <div className="text-slate-500">
          <span className="animate-pulse">▋</span>
        </div>
      </div>
    </div>
  )
}

// Главный компонент
export default function App() {
  const [task, setTask] = useState('')
  const [isRunning, setIsRunning] = useState(false)
  const [systemStatus, setSystemStatus] = useState(null)
  const [currentMission, setCurrentMission] = useState(null)
  const [activeAgent, setActiveAgent] = useState(null)
  const [isDark, setIsDark] = useState(true)
  const [logs, setLogs] = useState([
    { time: '00:00:00', message: '$ system_init --status success', type: 'success' },
    { time: '00:00:01', message: '→ Singularity Core v1.0 загружен', type: 'info' },
    { time: '00:00:02', message: '→ Агенты в режиме ожидания...', type: 'default' },
  ])

  const agents = [
    { id: 1, name: 'СТРАТЕГ', role: 'Планирование', icon: '🧠', statusIdle: 'В ожидании задачи', statusActive: 'Анализирует цель...' },
    { id: 2, name: 'РАЗРАБОТЧИК', role: 'Кодинг', icon: '⚡', statusIdle: 'Режим сна', statusActive: 'Пишет код...' },
    { id: 3, name: 'РЕВЬЮЕР', role: 'Проверка', icon: '🔍', statusIdle: 'Готов к проверке', statusActive: 'Сканирует...' },
    { id: 4, name: 'БЕЗОПАСНИК', role: 'Защита', icon: '🛡️', statusIdle: 'Мониторинг', statusActive: 'Аудит безопасности...' },
  ]

  // Проверка статуса системы
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await fetch(`${API_URL}/`)
        const data = await res.json()
        setSystemStatus(data)
        addLog('→ Подключение к API установлено', 'success')
      } catch (e) {
        addLog('✗ Ошибка подключения к API', 'error')
        setSystemStatus({ status: 'Offline' })
      }
    }
    checkStatus()
  }, [])

  // Polling статуса миссии
  useEffect(() => {
    if (!currentMission) return
    
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_URL}/mission/${currentMission}`)
        const data = await res.json()
        
        if (data.status === 'completed') {
          setIsRunning(false)
          setActiveAgent(null)
          addLog('✓ Миссия завершена успешно!', 'success')
          setCurrentMission(null)
        } else if (data.status === 'failed') {
          setIsRunning(false)
          setActiveAgent(null)
          addLog('✗ Миссия провалена', 'error')
          setCurrentMission(null)
        }
      } catch (e) {
        console.error(e)
      }
    }, 3000)
    
    return () => clearInterval(interval)
  }, [currentMission])

  // Симуляция активности агентов
  useEffect(() => {
    if (!isRunning) return
    
    let agentIndex = 0
    const interval = setInterval(() => {
      setActiveAgent(agents[agentIndex].id)
      addLog(`→ ${agents[agentIndex].name}: ${agents[agentIndex].statusActive}`, 'info')
      agentIndex = (agentIndex + 1) % agents.length
    }, 4000)
    
    return () => clearInterval(interval)
  }, [isRunning])

  const addLog = (message, type = 'default') => {
    const time = new Date().toLocaleTimeString('ru-RU', { hour12: false })
    setLogs(prev => [...prev, { time, message, type }])
  }

  const startMission = async () => {
    if (!task.trim()) {
      addLog('✗ Введите задачу для Роя', 'error')
      return
    }

    setIsRunning(true)
    setActiveAgent(1)
    addLog(`$ start_mission --task "${task}"`, 'default')
    addLog('→ Инициализация протокола Singularity...', 'info')

    try {
      const res = await fetch(`${API_URL}/launch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: task })
      })
      
      const data = await res.json()
      setCurrentMission(data.mission_id)
      addLog(`→ Миссия ${data.mission_id} запущена`, 'success')
      addLog('→ Рой начал выполнение задачи...', 'info')
    } catch (e) {
      addLog('✗ Ошибка запуска миссии', 'error')
      setIsRunning(false)
      setActiveAgent(null)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !isRunning) {
      startMission()
    }
  }

  return (
    <div className={`min-h-screen transition-colors duration-500 ${
      isDark ? 'bg-slate-950 text-slate-300' : 'bg-gradient-to-br from-slate-50 to-slate-100 text-slate-700'
    }`}>
      {/* Фоновые эффекты */}
      <div 
        className="fixed inset-0 pointer-events-none transition-opacity duration-500"
        style={{
          background: isDark 
            ? 'radial-gradient(ellipse at top, rgba(99, 102, 241, 0.15) 0%, transparent 50%)'
            : 'radial-gradient(ellipse at top, rgba(99, 102, 241, 0.08) 0%, transparent 50%)'
        }}
      />
      <div 
        className={`fixed inset-0 pointer-events-none transition-opacity duration-500 ${isDark ? 'opacity-30' : 'opacity-10'}`}
        style={{
          backgroundImage: `linear-gradient(${isDark ? 'rgba(99, 102, 241, 0.03)' : 'rgba(99, 102, 241, 0.05)'} 1px, transparent 1px), linear-gradient(90deg, ${isDark ? 'rgba(99, 102, 241, 0.03)' : 'rgba(99, 102, 241, 0.05)'} 1px, transparent 1px)`,
          backgroundSize: '50px 50px'
        }}
      />
      
      <div className="relative z-10 p-6 md:p-10">
        {/* Header */}
        <header className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center mb-12 gap-4">
          <div className="flex items-center gap-4">
            <div className={`
              w-12 h-12 rounded-xl flex items-center justify-center transition-colors duration-300
              ${isDark 
                ? 'bg-indigo-600/20 border border-indigo-500/30' 
                : 'bg-indigo-100 border border-indigo-200'}
            `}>
              <span className="text-2xl">◈</span>
            </div>
            <div>
              <h1 className={`text-2xl font-bold tracking-[0.2em] ${isDark ? 'text-white' : 'text-slate-800'}`}>
                SINGULARITY
              </h1>
              <p className="text-xs text-indigo-500 tracking-widest">AUTONOMOUS AI SWARM v1.0</p>
            </div>
          </div>
          
          <div className="flex items-center gap-6">
            {/* Theme Toggle */}
            <ThemeToggle isDark={isDark} onToggle={() => setIsDark(!isDark)} />
            
            <div className="text-right">
              <p className={`text-xs uppercase tracking-wider ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                System Status
              </p>
              <p className={`text-sm font-medium ${
                systemStatus?.status?.includes('Online') ? 'text-emerald-500' : 'text-red-500'
              }`}>
                {systemStatus?.status || 'Connecting...'}
              </p>
            </div>
            <div className={`w-4 h-4 rounded-full ${
              systemStatus?.status?.includes('Online') 
                ? 'bg-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.5)]' 
                : 'bg-red-500'
            }`} />
          </div>
        </header>

        <main className="max-w-6xl mx-auto space-y-8">
          {/* Input Area */}
          <div className={`
            rounded-2xl p-2 backdrop-blur-xl border transition-colors duration-300
            ${isDark 
              ? 'bg-slate-900/60 border-slate-800/50' 
              : 'bg-white border-slate-200 shadow-lg'}
          `}>
            <div className="relative">
              <input 
                type="text"
                className={`
                  w-full border-0 rounded-xl p-5 pr-40 text-lg
                  focus:outline-none focus:ring-2 focus:ring-indigo-500/50 
                  transition-all
                  ${isDark 
                    ? 'bg-slate-900/60 placeholder:text-slate-600 text-white' 
                    : 'bg-slate-50 placeholder:text-slate-400 text-slate-800'}
                `}
                placeholder="Опишите вашу цель... Рой выполнит её автономно"
                value={task}
                onChange={(e) => setTask(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isRunning}
              />
              <button 
                onClick={startMission}
                disabled={isRunning}
                className={`
                  absolute right-3 top-1/2 -translate-y-1/2 
                  px-6 py-3 rounded-xl font-medium text-sm tracking-wider
                  transition-all duration-300
                  ${isRunning 
                    ? isDark 
                      ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                      : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                    : 'bg-indigo-600 hover:bg-indigo-500 text-white hover:shadow-[0_0_30px_rgba(99,102,241,0.4)]'}
                `}
              >
                {isRunning ? (
                  <span className="flex items-center gap-2">
                    <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    В ПРОЦЕССЕ
                  </span>
                ) : 'ЗАПУСТИТЬ РОЙ'}
        </button>
            </div>
          </div>

          {/* Agents Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {agents.map(agent => (
              <AgentCard 
                key={agent.id}
                name={agent.name}
                role={agent.role}
                icon={agent.icon}
                status={activeAgent === agent.id ? agent.statusActive : agent.statusIdle}
                active={activeAgent === agent.id}
                isDark={isDark}
              />
            ))}
          </div>

          {/* Terminal */}
          <Terminal logs={logs} isDark={isDark} />

          {/* Footer Stats */}
          <div className="grid grid-cols-3 gap-4">
            <div className={`
              rounded-xl p-4 text-center backdrop-blur-xl border transition-colors duration-300
              ${isDark 
                ? 'bg-slate-900/60 border-slate-800/50' 
                : 'bg-white border-slate-200 shadow-sm'}
            `}>
              <p className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-slate-800'}`}>4</p>
              <p className={`text-xs uppercase tracking-wider ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                Агентов
              </p>
            </div>
            <div className={`
              rounded-xl p-4 text-center backdrop-blur-xl border transition-colors duration-300
              ${isDark 
                ? 'bg-slate-900/60 border-slate-800/50' 
                : 'bg-white border-slate-200 shadow-sm'}
            `}>
              <p className="text-2xl font-bold text-indigo-500">
                {currentMission ? '1' : '0'}
              </p>
              <p className={`text-xs uppercase tracking-wider ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                Активных миссий
              </p>
            </div>
            <div className={`
              rounded-xl p-4 text-center backdrop-blur-xl border transition-colors duration-300
              ${isDark 
                ? 'bg-slate-900/60 border-slate-800/50' 
                : 'bg-white border-slate-200 shadow-sm'}
            `}>
              <p className="text-2xl font-bold text-emerald-500">∞</p>
              <p className={`text-xs uppercase tracking-wider ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                Возможностей
              </p>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
