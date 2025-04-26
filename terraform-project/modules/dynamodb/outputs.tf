###############################
# modules/dynamodb/outputs.tf
###############################

output "classes_trips_table_name" {
  value = aws_dynamodb_table.ClassesTrips.name
}

output "locations_table_name" {
  value = aws_dynamodb_table.Locations.name
}

output "locations_table_stream_arn" {
  value = aws_dynamodb_table.Locations.stream_arn
}

output "user_profiles_table_name" {
  value = aws_dynamodb_table.UserProfiles.name
}