output "nameservers" {
  description = "Route53 네임서버"
  value       = data.aws_route53_zone.main.name_servers
}

output "certificate_arn" {
  description = "ACM 인증서 ARN"
  value       = aws_acm_certificate_validation.main.certificate_arn
}

output "zone_id" {
  description = "Route53 호스팅 영역 ID"
  value       = data.aws_route53_zone.main.zone_id
}
