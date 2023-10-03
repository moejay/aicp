provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

resource "google_project" "this_project" {
  name       = var.project_name
  project_id = var.project_id
}

resource "google_project_service" "pubsub" {
  project = google_project.this_project.project_id
  service = "pubsub.googleapis.com"
}

resource "google_project_service" "storage" {
  project = google_project.this_project.project_id
  service = "storage.googleapis.com"
}

resource "google_pubsub_topic" "worker_request" {
  name = "worker_request"
  depends_on = [google_project_service.pubsub]
}

resource "google_pubsub_topic" "worker_response" {
  name = "worker_response"
  depends_on = [google_project_service.pubsub]
}

resource "google_storage_bucket" "worker_outputs" {
  name          = var.bucket_name
  location      = var.bucket_location
  force_destroy = var.bucket_force_destroy
  storage_class = "STANDARD"

  public_access_prevention    = "enforced"
  uniform_bucket_level_access = true

  depends_on = [google_project_service.storage]
}

resource "google_service_account" "worker" {
  account_id   = "worker"
  display_name = "Worker Service Account"
  description  = "Service account for workers with Pub/Sub and Bucket access."
}

resource "google_project_iam_binding" "worker_pubsub_access" {
  project = var.project_id
  role    = "roles/pubsub.editor"

  members = [
    "serviceAccount:${google_service_account.worker.email}"
  ]
}

// Grant the Service Account Storage Object Admin (read/write) access to the bucket
resource "google_storage_bucket_iam_binding" "bucket_access" {
  bucket = google_storage_bucket.worker_outputs.name
  role   = "roles/storage.objectAdmin"

  members = [
    "serviceAccount:${google_service_account.worker.email}"
  ]
}

// Grant the Service Account Storage Object Viewer role for signed URL generation
resource "google_project_iam_binding" "signed_url_access" {
  project = var.project_id
  role    = "roles/storage.objectViewer"

  members = [
    "serviceAccount:${google_service_account.worker.email}"
  ]
}

// Download the worker service account json
resource "google_service_account_key" "worker_sa_key" {
  service_account_id = google_service_account.worker.name

  # This determines the format of the key. "JSON" is recommended.
  key_algorithm = "KEY_ALG_RSA_2048"
  public_key_type = "TYPE_X509_PEM_FILE"
}
