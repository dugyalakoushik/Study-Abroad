output "lambda_function_names" {
  value = [for f in aws_lambda_function.loc_notify : f.function_name]
}

output "lambda_function_arns" {
  value = { for name, f in aws_lambda_function.loc_notify : name => f.arn }
}
