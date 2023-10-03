variable "project_name" {
  description = "The name of the project."
  type        = string
}

variable "project_id" {
  description = "The ID of the project."
  type        = string
}

variable "region" {
  description = "The region to deploy to."
  default     = "us-east1"
}

variable "zone" {
  description = "The zone within the chosen region."
  default     = "us-east1-a"
}

variable "bucket_name" {
  description = "The name of the storage bucket."
  type        = string
}

variable "bucket_location" {
  description = "The location of the storage bucket."
  default     = "US"
}

variable "bucket_force_destroy" {
  description = "A boolean that indicates all objects should be deleted when the bucket is destroyed."
  default     = false
}
