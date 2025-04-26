##############################################
# terraform-project/outputs.tf (root)
##############################################

# Outputs for the Cognito module
output "user_pool_id" {
  value = module.cognito.user_pool_id
}

output "user_pool_client_id" {
  value = module.cognito.user_pool_client_id
}

output "user_pool_client_id_secret" {
  value     = module.cognito.user_pool_client_id_secret
  sensitive = true
}

# Outputs for the DynamoDB module
output "dynamodb_output" {
  value = {
    classes_trips_table_name = module.dynamodb.classes_trips_table_name
    locations_table_name     = module.dynamodb.locations_table_name
    user_profiles_table_name = module.dynamodb.user_profiles_table_name
  }
}

# Outputs for the SNS module
output "sns_topic_output" {
  value = module.sns.sns_topic_output
}

# Outputs for the s3 module
output "s3_bucket_name" {
  value = module.s3.s3_bucket_name
}
output "s3_bucket_arn" {
  value = module.s3.s3_bucket_arn
}
output "s3_bucket_website_endpoint" {
  value = module.s3.s3_bucket_website_endpoint
}



# Outputs for the CloudFront module
output "cloudfront_distribution_id" {
  value = module.cloudfront.cloudfront_distribution_id
}
output "cloudfront_distribution_domain" {
  value = module.cloudfront.cloudfront_distribution_domain
}

output "cloudfront_distribution_domain_name" {
  value = module.cloudfront.cloudfront_distribution_domain_name
}

# Lambda Auth Module Outputs
output "lambda_auth_function_names" {
  value = module.lambda_auth.lambda_function_names
}

output "lambda_auth_function_arns" {
  value = module.lambda_auth.lambda_function_arns
}


output "lambda_classes_function_names" {
  value = module.lambda_classes.lambda_function_names
}

output "lambda_classes_function_arns" {
  value = module.lambda_classes.lambda_function_arns
}

output "lambda_faculty_function_names" {
  value = module.lambda_faculty.lambda_function_names
}

output "lambda_students_function_names" {
  value = module.lambda_students.lambda_function_names
}

output "lambda_students_function_arns" {
  value = module.lambda_students.lambda_function_arns
}

output "lambda_loc_notify_function_names" {
  value = module.lambda_loc_notify.lambda_function_names
}

output "lambda_loc_notify_function_arns" {
  value = module.lambda_loc_notify.lambda_function_arns
}

#API gateway outputs
output "apigateway_studyabroad_rest_api_id" {
  value = module.apigateway-studyabroad.rest_api_id
}

output "apigateway_studyabroad_execution_arn" {
  value = module.apigateway-studyabroad.rest_api_execution_arn
}

output "apigateway_studyabroad_stage_name" {
  value = module.apigateway-studyabroad.stage_name
}

output "apigateway_studyabroad_invoke_url" {
  value = module.apigateway-studyabroad.invoke_url
}
