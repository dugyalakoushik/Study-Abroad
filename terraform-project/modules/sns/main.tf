#################################
# modules/sns/main.tf
#################################

resource "aws_sns_topic" "faculty_emergency" {
  name         = "FacultyEmergencyNotifications"
  display_name = "Faculty Emergency Notifications"
}

resource "aws_sns_topic" "student_checkin" {
  name         = "StudentNotificationsCheck"
  display_name = "Location Check In Notification"
}

resource "aws_sns_topic_policy" "faculty_emergency_policy" {
  arn    = aws_sns_topic.faculty_emergency.arn
  policy = jsonencode({
    Version = "2008-10-17",
    Id      = "__default_policy_ID",
    Statement = [
      {
        Sid       = "__default_statement_ID",
        Effect    = "Allow",
        Principal = { AWS = "*" },
        Action = [
          "SNS:Publish",
          "SNS:RemovePermission",
          "SNS:SetTopicAttributes",
          "SNS:DeleteTopic",
          "SNS:ListSubscriptionsByTopic",
          "SNS:GetTopicAttributes",
          "SNS:AddPermission",
          "SNS:Subscribe"
        ],
        Resource  = aws_sns_topic.faculty_emergency.arn,
        Condition = {
          StringEquals = {
            "AWS:SourceOwner" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}

resource "aws_sns_topic_policy" "student_checkin_policy" {
  arn    = aws_sns_topic.student_checkin.arn
  policy = jsonencode({
    Version = "2008-10-17",
    Id      = "__default_policy_ID",
    Statement = [
      {
        Sid       = "__default_statement_ID",
        Effect    = "Allow",
        Principal = { AWS = "*" },
        Action = [
          "SNS:Publish",
          "SNS:RemovePermission",
          "SNS:SetTopicAttributes",
          "SNS:DeleteTopic",
          "SNS:ListSubscriptionsByTopic",
          "SNS:GetTopicAttributes",
          "SNS:AddPermission",
          "SNS:Subscribe"
        ],
        Resource  = aws_sns_topic.student_checkin.arn,
        Condition = {
          StringEquals = {
            "AWS:SourceOwner" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}

data "aws_caller_identity" "current" {}
