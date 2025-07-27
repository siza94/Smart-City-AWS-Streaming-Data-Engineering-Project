# Smart City End-to-End Real-Time Data Streaming Pipeline 🚦🏙️

## 🌍 Project Overview

This project implements a full real-time data engineering pipeline simulating a smart city environment. By integrating IoT devices, stream processing, and cloud services, the solution enables continuous monitoring and analysis of critical urban data — such as traffic flow, weather conditions, GPS locations, and emergency incidents — empowering city officials with real-time insights for smarter urban management.

## ⚙️ Key Features

- **Real-time data ingestion** from simulated IoT sensors
- **Kafka-based message streaming** with Docker orchestration
- **Spark Structured Streaming** for processing live data streams
- **AWS S3, Glue, Redshift, Athena, and QuickSight** for cloud storage, ETL, querying, and visualization
- **Dashboards** for vehicle telemetry, congestion, weather alerts, and emergency incidents



## 🔧 Technologies Used

| Category            | Tools / Services                                |
|---------------------|--------------------------------------------------|
| Ingestion           | Apache Kafka, Zookeeper, Docker                  |
| Stream Processing   | Apache Spark Structured Streaming, Python        |
| Storage             | AWS S3, AWS Glue, AWS Redshift                   |
| Querying            | AWS Athena                                       |
| Visualization       | Amazon QuickSight                                |
| Containerization    | Docker, Docker Compose                           |
| Others              | IAM Roles, Python scripts, Simulated IoT data    |

## 🧪 Use Case Scenario

The simulated use case involves a vehicle traveling between major cities while sending data like:

- Vehicle speed & telemetry
- GPS coordinates
- Weather reports
- Emergency incidents (accidents, alerts, hazards)

This pipeline processes, stores, and visualizes the data in near real-time — ideal for smart traffic management, public safety, and city infrastructure optimization.

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- AWS account (with access to S3, Glue, Athena, Redshift, QuickSight)
- Python 3.8+
- AWS CLI configured

### 1. Clone the Repository
```bash
git clone https://github.com/siza94/Smart-City-AWS-Streaming-Data-Engineering-Project.git
cd python jobs/smart_city.py
```


### 2. Start Kafka and Zookeeper
```bash
docker-compose up -d
```

### 3. Produce, Stream Data to AWS S3 bucket
Simulate IoT sensor data by pushing to Kafka topics

Launch Spark job:

```bash
docker exec -it smart_city-spark-master-1 spark-submit --master spark://spark-master:7077 --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.apache.hadoop:hadoop-aws:3.3.1,com.amazonaws:aws-java-sdk:1.11.469 jobs/spark-city.py
```

### 4. AWS Configuration
Configure S3 bucket and IAM roles

Run Glue Crawler to catalog data

Use Athena/Redshift for querying

Connect QuickSight to create interactive dashboards

📊 Dashboard Highlights
Vehicle Speed KPIs

Emergency Incident Tracker

Weather Impact Trends

Map Visualizations of Routes

Heatmaps of Congestion Points

Time Series Analysis by Location & Type

📘 Documentation
Full project report and detailed technical documentation can be found here:
👉 Smart City Project Report (PDF)

Acknowledgments
Special thanks to Yunus for guidance throughout this project and to the open-source community for the amazing tools.
