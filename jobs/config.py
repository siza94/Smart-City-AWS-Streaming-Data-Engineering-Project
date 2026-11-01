import os

configuration = {
    "AWS_ACCESS_KEY": os.getenv("AWS_ACCESS_KEY", ""),
    "AWS_SECRET_KEY": os.getenv("AWS_SECRET_KEY", ""),
    "S3_BUCKET": os.getenv("S3_BUCKET", "spark-streaming-data-2025"),
}
