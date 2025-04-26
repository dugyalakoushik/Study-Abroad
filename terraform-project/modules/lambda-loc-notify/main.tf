locals {
  lambda_functions = [
    {
      name        = "locationsFaculty"
      timeout     = 3
      runtime     = "nodejs22.x"
      role        = var.locations_faculty_role
      handler     = "index.handler"
      environment = {}
    },
    {
      name        = "FacultyEmergencyNotification"
      timeout     = 3
      runtime     = "python3.13"
      role        = var.lambda_sns_role
      handler     = "lambda_function.lambda_handler"
      environment = {
        CLASSES_TRIPS_TABLE   = var.classes_table
        USERS_TABLE           = var.user_table
        FACULTY_TOPIC_ARN     = var.faculty_sns_arn
      }
    },
    {
      name        = "storeLocation"
      timeout     = 3
      runtime     = "nodejs22.x"
      role        = var.store_location_role
      handler     = "index.handler"
      environment = {}
    }
  ]
}

resource "aws_lambda_function" "loc_notify" {
  for_each = {
    for fn in local.lambda_functions : fn.name => fn
  }

  function_name = each.key
  role          = each.value.role
  runtime       = each.value.runtime
  handler       = each.value.handler
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
