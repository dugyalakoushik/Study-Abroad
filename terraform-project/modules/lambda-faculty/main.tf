locals {
  lambda_functions = [
    {
      name        = "createStatus"
      timeout     = 3
      role        = var.lambda_role_arn
      environment = {
        DYNAMODB_TABLE_NAME = var.classes_table
      }
    },
    {
      name        = "GetFacultyfromUserProfiles"
      timeout     = 3
      role        = var.lambda_role_arn
      environment = {
        TRIP_TABLE  = var.classes_table
        USERS_TABLE = var.user_table
      }
    },
    {
      name        = "AddFacultyinClass"
      timeout     = 3
      role        = var.lambda_role_arn
      environment = {
        CLS_TABLE = var.classes_table
      }
    },
    {
      name        = "GetFacultyFromClass"
      timeout     = 3
      role        = var.lambda_role_arn
      environment = {
        CLS_TABLE = var.classes_table
      }
    },
    {
      name        = "notifyStudents"
      timeout     = 3
      role        = var.lambda_sns_role_arn
      environment = {
        CLASSES_TRIPS_TABLE    = var.classes_table
        USERS_TABLE            = var.user_table
        STUDENT_SNS_TOPIC_ARN  = var.student_sns_topic_arn
      }
    },
    {
      name        = "FacultyDeletefromClass"
      timeout     = 3
      role        = var.lambda_role_arn
      environment = {
        CLS_TABLE = var.classes_table
      }
    }
  ]
}

resource "aws_lambda_function" "faculty" {
  for_each = {
    for fn in local.lambda_functions : fn.name => fn
  }

  function_name = each.key
  role          = each.value.role
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
