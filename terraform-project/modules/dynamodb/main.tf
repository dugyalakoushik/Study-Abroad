###############################
# modules/dynamodb/main.tf
###############################

resource "aws_dynamodb_table" "ClassesTrips" {
  name         = "ClassesTrips"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "classId"

  attribute {
    name = "classId"
    type = "S"
  }
}

resource "aws_dynamodb_table" "Locations" {
  name         = "Locations"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  range_key    = "timestamp"

  stream_enabled    = true
  stream_view_type  = "NEW_AND_OLD_IMAGES"

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }
}

resource "aws_dynamodb_table" "UserProfiles" {
  name         = "UserProfiles"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "userId"

  attribute {
    name = "userId"
    type = "S"
  }
}
