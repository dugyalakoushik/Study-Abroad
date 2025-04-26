output "lambda_function_names" {
  value = [for f in aws_lambda_function.students : f.function_name]
}

output "lambda_function_arns" {
  value = { for name, fn in aws_lambda_function.students : name => fn.arn }
}
