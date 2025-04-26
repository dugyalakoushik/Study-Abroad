#########################
# modules/cognito/main.tf
#########################

resource "aws_cognito_user_pool" "main" {
  name = "User pool - aoprbd"
  


  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
    temporary_password_validity_days = 1
  }

  auto_verified_attributes = ["email"]
  alias_attributes         = ["email", "phone_number"]
  mfa_configuration        = "OFF"

  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }

  sms_configuration {
    external_id = "d29a2706-095e-46b9-94fe-a64f4f0e9f42"
    sns_caller_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/service-role/CognitoIdpSNSServiceRole"
    sns_region     = var.aws_region
  }

  admin_create_user_config {
    allow_admin_create_user_only = false
  }

  username_configuration {
    case_sensitive = false
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
    recovery_mechanism {
      name     = "verified_phone_number"
      priority = 2
    }
  }

  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
    email_subject = "Your verification code - Study Abroad"
    email_message = <<EOF
Thanks for registering on Study Abroad application
Your verification code is {####}.
EOF
    email_subject_by_link = "Your verification link"
    email_message_by_link = <<EOF
Welcome to Study Abroad Application. 
Please click the link below to verify your email address. {##Verify Email##}
EOF
    sms_message = "Your verification code is {####}."
  }

  schema {
    name     = "email"
    attribute_data_type = "String"
    required = true
    mutable  = true
    string_attribute_constraints {
      min_length = 0
      max_length = 2048
    }
  }

  schema {
    name     = "custom:userRole"
    attribute_data_type = "String"
    required = false
    mutable  = true
    string_attribute_constraints {}
  }
}

resource "aws_cognito_user_pool_client" "client" {
  name         = "Study Abroad App"
  user_pool_id = aws_cognito_user_pool.main.id

  generate_secret                  = true
  refresh_token_validity          = 60
  access_token_validity           = 60
  id_token_validity               = 60
  token_validity_units {
    access_token = "minutes"
    id_token     = "minutes"
    refresh_token = "minutes"
  }

  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["email", "openid", "phone"]
  supported_identity_providers         = ["COGNITO"]
  callback_urls                        = ["http://localhost"]

  explicit_auth_flows = [
    "ALLOW_ADMIN_USER_PASSWORD_AUTH",
    "ALLOW_CUSTOM_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_USER_SRP_AUTH"
  ]

  prevent_user_existence_errors = "ENABLED"
}


resource "aws_cognito_user_group" "admin" {
  user_pool_id = aws_cognito_user_pool.main.id
  name         = "admin"
}

resource "aws_cognito_user_group" "student" {
  user_pool_id = aws_cognito_user_pool.main.id
  name         = "student"
}

resource "aws_cognito_user_group" "faculty" {
  user_pool_id = aws_cognito_user_pool.main.id
  name         = "faculty"
}

data "aws_caller_identity" "current" {}
