output "lambda_function_names" {
  value = [for f in aws_lambda_function.classes : f.function_name]
}

output "lambda_function_arns" {
  value = { for name, func in aws_lambda_function.classes : name => func.arn }
}
