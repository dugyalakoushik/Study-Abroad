output "user_pool_id" {
  value = aws_cognito_user_pool.main.id
}

output "user_pool_client_id" {
  value = aws_cognito_user_pool_client.client.id
}

output "user_pool_client_id_secret" {
  value = aws_cognito_user_pool_client.client.client_secret
}