variable "lambda_role_arn" {
  description = "IAM Role ARN"
  type        = string
}

variable "handler" {
  default = "lambda_function.lambda_handler"
}

variable "runtime" {
  default = "python3.13"
}

variable "timeout" {
  default = 3
}

variable "memory_size" {
  default = 128
}

variable "user_pool_id" {
  type = string
}

variable "cognito_client_id" {
  type = string
}

variable "cognito_client_secret" {
  type = string
}

variable "user_table" {
  type = string
}

variable "classes_table" {
  type = string
}

variable "faculty_sns_arn" {
  type    = string
  default = ""
}

variable "student_sns_arn" {
  type    = string
  default = ""
}
