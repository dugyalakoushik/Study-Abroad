locals {
  lambda_functions = [
    {
      name                = "login"
      timeout             = 10
      environment         = {
        COGNITO_CLIENT_SECRET = var.cognito_client_secret
        USER_TABLE            = var.user_table
        CLASSES_TABLE         = var.classes_table
        COGNITO_CLIENT_ID     = var.cognito_client_id
        USER_POOL_ID          = var.user_pool_id
      }
    },
    {
      name                = "RefreshToken"
      timeout             = 3
      environment         = {
        COGNITO_CLIENT_SECRET = var.cognito_client_secret
        COGNITO_CLIENT_ID     = var.cognito_client_id
        USER_POOL_ID          = var.user_pool_id
      }
    },
    {
      name                = "createUser"
      timeout             = 3
      environment         = {
        SNS_TOPIC_ARN         = var.faculty_sns_arn
        STUDENT_SNS_TOPIC_ARN = var.student_sns_arn
        COGNITO_CLIENT_SECRET = var.cognito_client_secret
        COGNITO_CLIENT_ID     = var.cognito_client_id
        USER_POOL_ID          = var.user_pool_id
        USER_TABLE            = var.user_table
      }
    },
        {
      name        = "resetPassword"
      timeout     = 3
      environment = {
        COGNITO_CLIENT_SECRET = var.cognito_client_secret
        COGNITO_CLIENT_ID     = var.cognito_client_id
        USER_POOL_ID          = var.user_pool_id
      }
    },

  ]
}

resource "aws_lambda_function" "auth" {
  for_each = {
    for lambda in local.lambda_functions : lambda.name => lambda
  }

  function_name = each.value.name
  role          = var.lambda_role_arn
  handler       = var.handler
  runtime       = var.runtime
  timeout       = each.value.timeout
  memory_size   = var.memory_size
  architectures = ["x86_64"]
  publish       = true

  filename         = "${path.module}/placeholder.zip"
  source_code_hash = filebase64sha256("${path.module}/placeholder.zip")

  environment {
    variables = each.value.environment
  }

  tracing_config {
    mode = "PassThrough"
  }
}

