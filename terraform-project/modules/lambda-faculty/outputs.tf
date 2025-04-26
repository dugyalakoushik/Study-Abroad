output "lambda_function_names" {
  value = [for fn in aws_lambda_function.faculty : fn.function_name]
}

output "lambda_function_arns" {
  value = { for name, fn in aws_lambda_function.faculty : name => fn.arn }
}
