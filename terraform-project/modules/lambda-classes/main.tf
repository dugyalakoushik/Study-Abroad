locals {
  lambda_functions = [
    {
      name        = "GetNameFaculty"
      timeout     = 3
      environment = {
        CLASSES_TABLE = var.classes_table
      }
    },
    {
      name        = "getClass"
      timeout     = 3
      environment = {
        CLASSES_TABLE = var.classes_table
      }
    },
    {
      name        = "deleteClass"
      timeout     = 3
      environment = {
        CLASSES_TABLE = var.classes_table
      }
    },
    {
      name        = "GetStudentwithinClass"
      timeout     = 3
      environment = {
        CLASSES_TABLE = var.classes_table
      }
    },
    {
      name        = "createClasses"
      timeout     = 3
      environment = {
        CLASSES_TABLE = var.classes_table
      }
    }
  ]
}

resource "aws_lambda_function" "classes" {
  for_each = {
    for lambda in local.lambda_functions : lambda.name => lambda
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
