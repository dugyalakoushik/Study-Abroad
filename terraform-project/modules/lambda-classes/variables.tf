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

variable "classes_table" {
  description = "DynamoDB table name for classes"
  type        = string
}
