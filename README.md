# 🚀 SNMP Huawei Docker Monitoring System

![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![Python](https://img.shields.io/badge/Python-3.x-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

A production-ready, containerized SNMP trap processing system tailored
for Huawei network environments.\
Designed for NOC engineers and DevOps teams, this project enables
scalable, real-time trap ingestion, parsing, and storage using a clean
microservice-style architecture.

------------------------------------------------------------------------

## ✨ Key Highlights

-   📡 High-performance SNMP trap receiver (Huawei optimized)
-   🐳 Fully containerized deployment (Docker Compose)
-   🗄️ Reliable PostgreSQL backend
-   ⚡ Real-time alarm ingestion pipeline
-   🧩 Modular and extensible Python architecture
-   🔐 Environment-driven configuration
-   🛠️ CLI utilities for operations & debugging

------------------------------------------------------------------------

## 🏗️ Architecture Overview

    Huawei Devices  --->  SNMP Traps  --->  Python Receiver  --->  PostgreSQL
                                             |
                                             └── CLI / Debug Tools

------------------------------------------------------------------------

## 📁 Project Structure

    snmp_huawei_docker/
    ├── app/
    │   ├── pysnmp_trap_receiver.py   # Core SNMP listener
    │   ├── cli_db.py                 # Local DB access tool
    │   ├── cli_db_docker.py          # Docker DB access
    │   └── how_to_run.txt
    ├── Dockerfile
    ├── docker-compose.yml
    ├── requirements.txt
    ├── full_schema.sql               # DB schema
    ├── reset_db.sh                   # Reset utility
    ├── .env                          # Configuration
    └── db_check.txt

------------------------------------------------------------------------

## ⚙️ Requirements

-   Docker & Docker Compose
-   Linux server (recommended)
-   Python 3.x (optional for local runs)

------------------------------------------------------------------------

## 🚀 Quick Start

### 1. Clone Repository

    git clone https://github.com/mizan23/snmp_huawei_docker.git
    cd snmp_huawei_docker

### 2. Configure Environment

Edit `.env`:

    POSTGRES_USER=your_user
    POSTGRES_PASSWORD=your_password
    POSTGRES_DB=snmp_db

### 3. Deploy

    docker-compose up -d --build

### 4. Verify

    docker ps

------------------------------------------------------------------------

## 📡 SNMP Processing

-   Listens on UDP port **162**
-   Parses Huawei SNMP traps
-   Stores structured data into PostgreSQL

------------------------------------------------------------------------

## 🗄️ Database Setup

    docker exec -i <db_container> psql -U <user> -d <db> < full_schema.sql

------------------------------------------------------------------------

## 🧪 Operations & Debugging

### Access DB

    python app/cli_db.py

### Inside Docker

    python app/cli_db_docker.py

------------------------------------------------------------------------

## 🔄 Maintenance

### Reset Database

    ./reset_db.sh

------------------------------------------------------------------------

## 🔐 Security Best Practices

-   Never commit `.env` with real credentials
-   Use secrets management in production
-   Restrict SNMP access via firewall rules

------------------------------------------------------------------------

## 📌 Use Cases

-   Telecom NOC monitoring
-   Huawei alarm ingestion systems
-   SNMP lab simulations
-   Event-driven monitoring pipelines

------------------------------------------------------------------------

## 🛣️ Roadmap

-   Web dashboard (React + API)
-   Kafka streaming integration
-   Alerting (WhatsApp / Email / Slack)
-   Correlation engine for alarms

------------------------------------------------------------------------

## 👨‍💻 Author

**Mizanur Rahman**\
📧 mizanur.eee23@gmail.com\
🔗 https://github.com/mizan23

------------------------------------------------------------------------

## 📄 License

MIT License

------------------------------------------------------------------------

## ⭐ Support

If this project helps you, consider giving it a ⭐ on GitHub!
