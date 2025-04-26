output "s3_bucket_name" {
  value = aws_s3_bucket.frontend.bucket
}

output "s3_bucket_arn" {
  value = aws_s3_bucket.frontend.arn
}

output "s3_bucket_website_endpoint" {
  value = aws_s3_bucket_website_configuration.frontend_website.website_endpoint
}

