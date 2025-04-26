locals {
  lambda_functions = [
    {
      name        = "getStudents"
      timeout     = 3
      environment = {
        TRIP_TABLE  = var.classes_table
        USERS_TABLE = var.user_table
      }
    },
    {
      name        = "AdminAddStudentinClass"
      timeout     = 3
      environment = {
        CLS_TABLE = var.classes_table
      }
    },
    {
      name        = "fetchCustomStatus"
      timeout     = 3
      environment = {
        DYNAMODB_TABLE = var.classes_table
      }
    },
    {
      name        = "GetStudsfromClassesTrips"
      timeout     = 3
      environment = {
        CLS_TABLE = var.classes_table
      }
    },
    {
      name        = "StudDeletefromClass"
      timeout     = 3
      environment = {
        CLS_TABLE = var.classes_table
      }
    }
  ]
}

resource "aws_lambda_function" "students" {
  for_each = {
    for fn in local.lambda_functions : fn.name => fn
  }

  function_name = each.key
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
