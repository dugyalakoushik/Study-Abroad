output "rest_api_id" {
  value = aws_api_gateway_rest_api.main.id
}

output "rest_api_execution_arn" {
  value = aws_api_gateway_rest_api.main.execution_arn
}

output "stage_name" {
  value = aws_api_gateway_stage.prod.stage_name
}

output "invoke_url" {
  value = "https://${aws_api_gateway_rest_api.main.id}.execute-api.${var.aws_region}.amazonaws.com/${aws_api_gateway_stage.prod.stage_name}"
}



