output "auth_service_public_ip" {
  description = "Public IP of the Auth Service"
  value       = aws_instance.auth_service.public_ip
}

output "inventory_service_public_ip" {
  description = "Public IP of the Inventory Service"
  value       = aws_instance.inventory_service.public_ip
}

output "orders_service_public_ip" {
  description = "Public IP of the Orders Service"
  value       = aws_instance.orders_service.public_ip
}

output "mongodb_private_ip" {
  description = "Private IP of MongoDB instance"
  value       = aws_instance.mongodb.private_ip
}

output "postgresql_endpoint" {
  description = "PostgreSQL RDS endpoint"
  value       = aws_db_instance.postgresql.endpoint
}

output "postgresql_connection_string" {
  description = "PostgreSQL connection string (without password)"
  value       = "postgresql://${var.db_username}@${aws_db_instance.postgresql.endpoint}/provesi"
  sensitive   = true
}

