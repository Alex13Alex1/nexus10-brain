```mermaid
flowchart TD
    subgraph Модули
        A1[Модуль арифметических операций]
        A2[Модуль обработки ввода]
        A3[Модуль вывода результатов]
        A4[Модуль обработки ошибок]
    end

    subgraph Потоки данных
        B1[Получение ввода]
        B2[Валидация]
        B3[Выполнение операции]
        B4[Обработка ошибок]
        B5[Вывод результата]
    end

    subgraph Интерфейсы
        C1[Пользовательский интерфейс]
        C2[Интерфейс модулей]
    end

    C1 -->|Ввод данных| B1
    B1 -->|Передача данных| A2
    A2 -->|Валидация данных| B2
    B2 -->|Передача данных| A1
    A1 -->|Выполнение операции| B3
    B3 -->|Обработка ошибок| A4
    A4 -->|Обработка ошибок| B4
    B4 -->|Передача результата| A3
    A3 -->|Вывод результата| B5
    B5 -->|Отображение результата| C1
    C2 -->|Взаимодействие с модулями| A1
    C2 -->|Взаимодействие с модулями| A2
    C2 -->|Взаимодействие с модулями| A3
    C2 -->|Взаимодействие с модулями| A4
```

This diagram represents the architecture of a Simple Calculator CLI, highlighting the modules, data flows, and interfaces involved in processing user input, performing arithmetic operations, handling errors, and displaying results.