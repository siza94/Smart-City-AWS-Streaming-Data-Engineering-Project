from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, expr
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, DoubleType, IntegerType

from config import configuration

def main():
    s3_bucket = configuration.get("S3_BUCKET", "spark-streaming-data-2025")

    spark = SparkSession.builder.appName("SmartCityStreaming")\
        .config("spark.jars.packages",
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
                "org.apache.hadoop:hadoop-aws:3.3.1,"
                "com.amazonaws:aws-java-sdk:1.11.469")\
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")\
        .config("spark.hadoop.fs.s3a.access.key", configuration.get("AWS_ACCESS_KEY"))\
        .config("spark.hadoop.fs.s3a.secret.key", configuration.get("AWS_SECRET_KEY"))\
        .config("spark.hadoop.fs.s3a.aws.credentials.provider",
                "org.apache.hadoop.fs.s3a.SimpleAwsCredentialsProvider")\
        .getOrCreate()

    # Adjust the log level to minimize the console output on executors
    spark.sparkContext.setLogLevel("WARN")

    # Get vehicle schema (v2: explicit latitude & longitude DoubleType fields)
    vehicleSchema = StructType([
        StructField("id", StringType(), True),
        StructField("deviceId", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("location", StringType(), True),
        StructField("latitude", DoubleType(), True),
        StructField("longitude", DoubleType(), True),
        StructField("speed", DoubleType(), True),
        StructField("direction", StringType(), True),
        StructField("make", StringType(), True),
        StructField("model", StringType(), True),
        StructField("year", IntegerType(), True),
        StructField("transmission", StringType(), True),
        StructField("bodyType", StringType(), True),
        StructField("fuelType", StringType(), True),
    ])

    # Get GPS schema
    gpsSchema = StructType([
        StructField("id", StringType(), True),
        StructField("deviceId", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("speed", DoubleType(), True),
        StructField("direction", StringType(), True),
        StructField("vehicleType", StringType(), True),
    ])

    # Get traffic schema (v2 fix: location StringType + typed latitude/longitude DoubleType)
    trafficSchema = StructType([
        StructField("id", StringType(), True),
        StructField("deviceId", StringType(), True),
        StructField("cameraId", StringType(), True),
        StructField("location", StringType(), True),
        StructField("latitude", DoubleType(), True),
        StructField("longitude", DoubleType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("snapshot", StringType(), True),
    ])

    # Get weather schema (v2 fix: location StringType + typed latitude/longitude DoubleType)
    weatherSchema = StructType([
        StructField("id", StringType(), True),
        StructField("deviceId", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("location", StringType(), True),
        StructField("latitude", DoubleType(), True),
        StructField("longitude", DoubleType(), True),
        StructField("temperature", DoubleType(), True),
        StructField("weatherCondition", StringType(), True),
        StructField("precipitation", DoubleType(), True),
        StructField("windSpeed", DoubleType(), True),
        StructField("humidity", DoubleType(), True),
        StructField("airQualityIndex", DoubleType(), True),
    ])

    # Get emergency schema
    emergencySchema = StructType([
        StructField("id", StringType(), True),
        StructField("deviceId", StringType(), True),
        StructField("incidentId", StringType(), True),
        StructField("type", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("location", StringType(), True),
        StructField("latitude", DoubleType(), True),
        StructField("longitude", DoubleType(), True),
        StructField("status", StringType(), True),
        StructField("description", StringType(), True),
    ])

    def read_kafka_topic(topic, schema):
        return (spark.readStream
                .format('kafka')
                .option('kafka.bootstrap.servers', 'broker:29092')
                .option('subscribe', topic)
                .option('startingOffsets', 'earliest')
                .load()
                .selectExpr('CAST(value AS STRING)')
                .select(from_json(col('value'), schema).alias('data'))
                .select('data.*')
                .withWatermark('timestamp', '2 minutes')
                )

    def streamWriter(input_df, checkpointFolder, output):
        # v2 upgrade: 60-second micro-batch trigger prevents S3 small-file proliferation
        return (input_df.writeStream
                .format('parquet')
                .option('checkpointLocation', checkpointFolder)
                .option('path', output)
                .outputMode('append')
                .trigger(processingTime='60 seconds')
                .start()
                )

    vehicleDF = read_kafka_topic('vehicle_data', vehicleSchema).alias('vehicle')
    gpsDF = read_kafka_topic('gps_data', gpsSchema).alias('gps')
    trafficDF = read_kafka_topic('traffic_data', trafficSchema).alias('traffic')
    weatherDF = read_kafka_topic('weather_data', weatherSchema).alias('weather')
    emergencyDF = read_kafka_topic('emergency_data', emergencySchema).alias('emergency')

    # v2 Upgrade: Watermarked stream-stream join on (deviceId, timestamp) producing a unified Silver corridor stream
    corridorSilverDF = (
        vehicleDF
        .join(
            weatherDF,
            expr("""
                vehicle.deviceId = weather.deviceId AND
                weather.timestamp >= vehicle.timestamp - interval 1 minute AND
                weather.timestamp <= vehicle.timestamp + interval 1 minute
            """),
            "inner"
        )
        .join(
            emergencyDF,
            expr("""
                vehicle.deviceId = emergency.deviceId AND
                emergency.timestamp >= vehicle.timestamp - interval 1 minute AND
                emergency.timestamp <= vehicle.timestamp + interval 1 minute
            """),
            "inner"
        )
        .select(
            col("vehicle.id").alias("vehicle_event_id"),
            col("vehicle.deviceId").alias("device_id"),
            col("vehicle.timestamp").alias("event_timestamp"),
            col("vehicle.latitude").alias("latitude"),
            col("vehicle.longitude").alias("longitude"),
            col("vehicle.speed").alias("speed_mph"),
            col("vehicle.direction").alias("direction"),
            col("weather.temperature").alias("temperature_c"),
            col("weather.weatherCondition").alias("weather_condition"),
            col("weather.precipitation").alias("precipitation_mm"),
            col("weather.windSpeed").alias("wind_speed_kmh"),
            col("weather.humidity").alias("humidity_pct"),
            col("weather.airQualityIndex").alias("air_quality_index"),
            col("emergency.incidentId").alias("incident_id"),
            col("emergency.type").alias("incident_type"),
            col("emergency.status").alias("incident_status")
        )
    )

    query1 = streamWriter(vehicleDF, f's3a://{s3_bucket}/checkpoints/vehicle_data',
                          f's3a://{s3_bucket}/data/vehicle_data')

    query2 = streamWriter(gpsDF, f's3a://{s3_bucket}/checkpoints/gps_data',
                          f's3a://{s3_bucket}/data/gps_data')

    query3 = streamWriter(trafficDF, f's3a://{s3_bucket}/checkpoints/traffic_data',
                          f's3a://{s3_bucket}/data/traffic_data')

    query4 = streamWriter(weatherDF, f's3a://{s3_bucket}/checkpoints/weather_data',
                          f's3a://{s3_bucket}/data/weather_data')

    query5 = streamWriter(emergencyDF, f's3a://{s3_bucket}/checkpoints/emergency_data',
                          f's3a://{s3_bucket}/data/emergency_data')

    query6 = streamWriter(corridorSilverDF, f's3a://{s3_bucket}/checkpoints/silver_corridor_telemetry',
                          f's3a://{s3_bucket}/data/silver_corridor_telemetry')

    spark.streams.awaitAnyTermination()


if __name__ == "__main__":
    main()
