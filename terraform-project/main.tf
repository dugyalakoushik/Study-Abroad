terraform {
  backend "s3" {
    bucket         = "study-abroad-terraform-state-bucket"  # replace with your S3 bucket name
    key            = "study-abroad/terraform.tfstate"   # organize by env if needed
    region         = "us-east-1"                    # this must be hardcoded or parameterized via TF_VAR
    #use_lockfile   = true  # or false              # optional: for state locking
    encrypt        = true
  }

}

provider "aws" {
  region = var.aws_region

}

module "cognito" {
  source = "./modules/cognito"
  aws_region = var.aws_region
}

module "dynamodb" {
  source = "./modules/dynamodb"
  aws_region = var.aws_region
}
  

module "sns" {
  source = "./modules/sns"
}


module "s3" {
  source      = "./modules/s3"
  bucket_name = "study-abroad-frontend-iac-creates" # <-- pass your actual bucket name
}


module "cloudfront" {
  source = "./modules/cloudfront"

  origin_domain_name = module.s3.s3_bucket_website_endpoint
  origin_id          = module.s3.s3_bucket_website_endpoint # same as domain_name for static sites
}

#lambda functions from here




module "lambda_auth" {
  source = "./modules/lambda-auth"

  lambda_role_arn        = "arn:aws:iam::277707101844:role/LambdaDynamoDBRole"
  user_pool_id           = module.cognito.user_pool_id
  cognito_client_id      = module.cognito.user_pool_client_id
  cognito_client_secret  = module.cognito.user_pool_client_id_secret
  user_table             = module.dynamodb.user_profiles_table_name
  classes_table          = module.dynamodb.classes_trips_table_name
  faculty_sns_arn        = module.sns.sns_topic_output["faculty_emergency_arn"]
  student_sns_arn        = module.sns.sns_topic_output["student_checkin_arn"]
}


module "lambda_classes" {
  source           = "./modules/lambda-classes"
  lambda_role_arn  = "arn:aws:iam::277707101844:role/LambdaDynamoDBRole"
  classes_table    = module.dynamodb.classes_trips_table_name
}

module "lambda_faculty" {
  source                 = "./modules/lambda-faculty"
  lambda_role_arn        = "arn:aws:iam::277707101844:role/LambdaDynamoDBRole"
  lambda_sns_role_arn    = "arn:aws:iam::277707101844:role/LambdaDynamoSNS"
  classes_table          = module.dynamodb.classes_trips_table_name
  user_table             = module.dynamodb.user_profiles_table_name
  student_sns_topic_arn  = module.sns.sns_topic_output["student_checkin_arn"]
}


module "lambda_students" {
  source            = "./modules/lambda-students"
  lambda_role_arn   = "arn:aws:iam::277707101844:role/LambdaDynamoDBRole"
  classes_table     = module.dynamodb.classes_trips_table_name
  user_table        = module.dynamodb.user_profiles_table_name
}

module "lambda_loc_notify" {
  source                 = "./modules/lambda-loc-notify"
  locations_faculty_role = "arn:aws:iam::277707101844:role/service-role/locationsFaculty-role-ezq5vzvs"
  lambda_sns_role        = "arn:aws:iam::277707101844:role/LambdaDynamoSNS"
  store_location_role    = "arn:aws:iam::277707101844:role/service-role/storeLocation-role-1vkpaydp"

  classes_table          = module.dynamodb.classes_trips_table_name
  user_table             = module.dynamodb.user_profiles_table_name
  faculty_sns_arn        = module.sns.sns_topic_output["faculty_emergency_arn"]
}

module "apigateway-studyabroad" {
  source = "./modules/apigateway-studyabroad"

  aws_region              = var.aws_region
  create_user_lambda_uri  = "arn:aws:apigateway:${var.aws_region}:lambda:path/2015-03-31/functions/${module.lambda_auth.lambda_function_arns["createUser"]}/invocations"
  create_user_lambda_name = "createUser"
}



  
