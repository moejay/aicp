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
