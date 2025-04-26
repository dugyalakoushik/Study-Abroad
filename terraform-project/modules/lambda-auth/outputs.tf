output "lambda_function_names" {
  value = [for f in aws_lambda_function.auth : f.function_name]
}

output "lambda_function_arns" {
  value = { for k, f in aws_lambda_function.auth : k => f.arn }
}
