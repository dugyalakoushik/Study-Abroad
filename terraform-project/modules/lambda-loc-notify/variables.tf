variable "locations_faculty_role" {
  type        = string
  description = "IAM role for locationsFaculty Lambda"
}

variable "lambda_sns_role" {
  type        = string
  description = "IAM role for FacultyEmergencyNotification Lambda"
}

variable "store_location_role" {
  type        = string
  description = "IAM role for storeLocation Lambda"
}

variable "classes_table" {
  type        = string
  description = "Name of ClassesTrips DynamoDB table"
}

variable "user_table" {
  type        = string
  description = "Name of UserProfiles DynamoDB table"
}

variable "faculty_sns_arn" {
  type        = string
  description = "ARN for Faculty SNS topic"
}

variable "memory_size" {
  default = 128
}
