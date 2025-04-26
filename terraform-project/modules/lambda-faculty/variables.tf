variable "lambda_role_arn" {
  type = string
  description = "Role ARN for faculty-related Lambdas"
}

variable "lambda_sns_role_arn" {
  type        = string
  description = "IAM Role with SNS publish access"
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

variable "classes_table" {
  type = string
}

variable "user_table" {
  type = string
}

variable "student_sns_topic_arn" {
  type = string
}
