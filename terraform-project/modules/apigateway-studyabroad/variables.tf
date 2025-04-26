variable "aws_region" {
  description = "AWS region for API Gateway endpoint URL"
  type        = string
}


variable "create_user_lambda_uri" {
  description = "Full URI for the Lambda integration"
  type        = string
}

variable "create_user_lambda_name" {
  description = "Lambda function name for permission"
  type        = string
}
