from google.cloud import storage, bigquery

PROJECT_ID = "nwr-data-platform"  # UPDATE THIS
BUCKET_NAME = "nwr-landing-zone-bronze"  # UPDATE THIS
DATASET_ID = "bronze"

storage_client = storage.Client(project=PROJECT_ID)
bq_client = bigquery.Client(project=PROJECT_ID)


def upload_to_gcs(local_file, gcs_path):
    """Uploads local file to the GCS Data Lake"""
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(local_file)
    print(f"Uploaded {local_file} to gs://{BUCKET_NAME}/{gcs_path}")
    return f"gs://{BUCKET_NAME}/{gcs_path}"


def load_bq_idempotent(gcs_uri, table_name, is_json=False, partition_field=None):
    """Loads data from GCS to BigQuery Bronze idempotently."""
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"

    # NEW LINE: Force drop the table if it exists so we can safely rebuild its partitioning
    bq_client.delete_table(table_id, not_found_ok=True)

    # 1. Base configuration
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON if is_json else bigquery.SourceFormat.CSV,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    # 2. Add CSV-specific configurations ONLY if it's a CSV
    if not is_json:
        job_config.skip_leading_rows = 1

    # 3. Handle massive fact table partitioning
    if partition_field:
        job_config.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY, field=partition_field
        )

    print(f"Triggering load for {table_id}...")
    load_job = bq_client.load_table_from_uri(gcs_uri, table_id, job_config=job_config)
    load_job.result()  # Wait for job to complete
    print(f"Successfully loaded {load_job.output_rows} rows into {table_id}")


if __name__ == "__main__":
    # 1. Hotel Guests (Dimension / SCD Source)
    hotel_gcs_uri = upload_to_gcs("hotel_guests.csv", "hotel/guests.csv")
    load_bq_idempotent(hotel_gcs_uri, "raw_hotel_guests", is_json=False)

    # 2. Casino Spins (Fact / Incremental Source)
    casino_gcs_uri = upload_to_gcs("casino_spins.json", "casino/spins_20261010.json")
    load_bq_idempotent(casino_gcs_uri, "raw_casino_spins", is_json=True, partition_field="transaction_ts")
