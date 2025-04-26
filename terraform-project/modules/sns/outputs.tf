output "sns_topic_output" {
  value = {
    faculty_emergency_arn = aws_sns_topic.faculty_emergency.arn,
    student_checkin_arn   = aws_sns_topic.student_checkin.arn
  }
}