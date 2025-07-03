# 🏦 Платформа анализа данных клиентов банковского сервиса

## 📌 Цель

Создание автоматизированной платформы для загрузки, хранения и визуализации данных клиентов банка с помощью PostgreSQL, Airflow и Superset.

---

## ⚙️ Технологии

- **PostgreSQL** — база данных
- **Apache Airflow** — автоматизация загрузки новых данных
- **Apache Superset** — аналитический дашборд
- **Docker** — контейнеризация компонентов

---

## 🚀 Развёртывание

### 1. Создание Docker-сети
```bash
docker network create bank-net
```

### 2. Запуск PostgreSQL
```bash
docker run -d \
  --name postgres_1 \
  --network=bank-net \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD='123' \
  -e POSTGRES_DB=credit_db \
  -v postgres_1_vol:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:15
```

### 3. Инициализация таблицы
```bash
apt-get update
apt-get install -y wget
apt-get install -y unzip 
```
```bash
wget https://9c579ca6-fee2-41d7-9396-601da1103a3b.selstorage.ru/credit_clients.csv -O credit_clients.csv
```
```bash
docker cp ./data/credit_clients.csv postgres_1:/tmp/credit_clients.csv
```
```bash
docker exec -it postgres_1 psql -U postgres
```
```sql
-- Создаём базу данных (если ещё не создана)
CREATE DATABASE credit_db;

-- Подключаемся к ней
\c credit_db

-- Создаём таблицу
CREATE TABLE IF NOT EXISTS clients (
    date DATE,
    customer_id BIGINT PRIMARY KEY,
    surname TEXT,
    credit_score INT,
    geography TEXT,
    gender TEXT,
    age INT,
    tenure INT,
    balance FLOAT,
    num_of_products INT,
    has_cr_card BOOLEAN,
    is_active_member BOOLEAN,
    estimated_salary FLOAT,
    exited BOOLEAN
);

-- Загружаем данные из файла
\copy clients FROM '/tmp/credit_clients.csv' DELIMITER ',' CSV HEADER;

-- Выходим
\q
```

### 4. Запуск Superset
```bash
docker run -d \
  --name superset \
  --network=bank-net \
  -e "SUPERSET_SECRET_KEY=$(openssl rand -base64 42)" \
  -p 8080:8088 \
  apache/superset
```
Cоздание пользователя
```bash
docker exec -it superset superset fab create-admin \
            --username admin \
            --firstname Superset \
            --lastname Admin \
            --email admin@superset.com \
            --password admin
```
username, password понадобятся для авторизации в Superset.

Обновляем внутреннюю БД Superset:
```bash
docker exec -it superset superset db upgrade
```
Запускаем сервер Superset:
```bash
docker exec -it superset superset init
```
В локальном терминале прокидываем соединение:
```bash
ssh -L  8080:localhost:8080 <user_name>@<ip-address>
```
Доступ: http://localhost:8080

### 5. Установка и запуск Airflow (на хосте Linux)
1. Установка miniconda3
```bash
mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm ~/miniconda3/miniconda.sh
```
```bash
source ~/miniconda3/bin/activate
```
```bash
conda init --all
```
```bash
conda create -n af python==3.12
```
```bash
conda activate af
```

2. Установка airflow
```bash
pip install "apache-airflow[celery]==2.10.5" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.5/constraints-3.12.txt"
```

```bash
pip install requests pandas
```

3. Инициализируем базу данных:
```bash
airflow db init
```

4. Создаем пользователя
```bash
airflow users create \
    --username admin \
    --firstname укажи_имя \
    --lastname укажи_фамилию \
    --role Admin \
    --email укажи@почту.com
```

5. устанавливаем драйвер для подключения к Postgres:
```bash
pip install apache-airflow-providers-postgres
```

6. Запускаем веб-сервер:
```bash
airflow webserver --port 8081
```

7. Запускаем планировщик (в отдельной консоли активируем созданное окружение):
```bash
airflow scheduler
```

Перемести папку dags в папку airflow

Использование Superset
Подключи базу данных (credit_db) в разделе Data → Databases

Использование Airflow
Подключи базу данных (credit_db) в разделе Admin → Connections

🔄 Автоматизация
DAG load_credit_clients_from_s3:
1. Каждый час загружает CSV из S3
2. Добавляет новых клиентов в таблицу clients
3. Обновления отображаются в Superset

📁 Структура проекта
```bash
Копировать
Редактировать
project/
├── dags/
│   └── load_credit_clients.py     # DAG для загрузки
├── scripts/
│   └── init_db.sql                # SQL для создания таблицы
├── README.md
```
🧠 Возможности для расширения
1. Мониторинг с Prometheus + Grafana
2. Уведомления при падении DAG
3. Docker Compose для упрощённого развёртывания