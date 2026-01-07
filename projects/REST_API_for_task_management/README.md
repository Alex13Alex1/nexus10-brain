# REST API Management System for Tasks

This Python script outlines a REST API management system for tasks using Flask and Flask-RESTful. The system includes modules for task management, user management, security, error handling, and API documentation.

## 🚀 Быстрый старт
```bash
pip install -r requirements.txt
python main_fixed.py
```

## 🐳 Docker
```bash
docker build -t project .
docker run project
```

## 📁 Структура проекта
```
project/
│
├── main_fixed.py
├── requirements.txt
└── Dockerfile
```

## 🏗️ Архитектура
```mermaid
flowchart TD
    subgraph TaskManagementModule
        direction TB
        A1[Flask 2.3.0] --> A2[Flask-RESTful 0.3.9]
        A2 --> A3[create_task(data)]
        A2 --> A4[get_task(task_id)]
        A2 --> A5[update_task(task_id, data)]
        A2 --> A6[delete_task(task_id)]
        A2 --> A7[Data Validation]
    end

    subgraph UserManagementModule
        direction TB
        B1[create_user(data)]
        B2[authenticate_user(credentials)]
        B3[authorize_user(user_id, action)]
    end

    subgraph SecurityModule
        direction TB
        C1[JWT Authentication]
        C2[Data Encryption via HTTPS]
    end

    subgraph ErrorHandlingAndLoggingModule
        direction TB
        D1[log_error(error_message)]
        D2[handle_error(error_code)]
    end

    subgraph APIDocumentationModule
        direction TB
        E1[Swagger]
        E2[generate_api_docs()]
    end

    subgraph DataFlow
        direction TB
        F1[Client] --> F2[HTTP Requests]
        F2 --> TaskManagementModule
        TaskManagementModule --> F3[Database]
        F3 --> F4[HTTP Responses]
        F4 --> F1

        F1 --> G1[Authentication Request]
        G1 --> SecurityModule
        SecurityModule --> G2[JWT Token]
        G2 --> F1

        F2 --> ErrorHandlingAndLoggingModule
        ErrorHandlingAndLoggingModule --> F4
    end

    subgraph APIInterface
        direction TB
        H1[POST /tasks]
        H2[GET /tasks/{task_id}]
        H3[PUT /tasks/{task_id}]
        H4[DELETE /tasks/{task_id}]
        H5[POST /users]
        H6[POST /auth/login]
    end

    APIDocumentationModule --> I1[Swagger UI]

    classDef module fill:#f9f,stroke:#333,stroke-width:2px;
    class TaskManagementModule,UserManagementModule,SecurityModule,ErrorHandlingAndLoggingModule,APIDocumentationModule module;
```

## 📋 Зависимости
```
Flask==2.3.0
Flask-RESTful==0.3.9
```

## 👥 Авторы
AI Project Factory v7.0

### Заключение

Разработанная архитектура для REST API управления задачами обеспечивает модульность, безопасность и удобство использования. Использование Flask и Flask-RESTful упрощает создание и поддержку API, а интеграция с JWT обеспечивает надежную аутентификацию и авторизацию. Документация через Swagger облегчает интеграцию для разработчиков, а обработка ошибок и логирование повышают надежность и удобство использования API.