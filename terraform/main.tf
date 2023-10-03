provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

resource "google_project" "new_project" {
  name       = var.project_name
  project_id = var.project_id
}

resource "google_project_service" "pubsub" {
  project = google_project.new_project.project_id
  service = "pubsub.googleapis.com"
}

resource "google_pubsub_topic" "StoryboardArtist_v1" {
  name = "StoryboardArtist_v1"
  depends_on = [google_project_service.pubsub]
}

resource "google_pubsub_topic" "MusicComposer_v1" {
  name = "MusicComposer_v1"
  depends_on = [google_project_service.pubsub]
}
