variable "public_key_path" {
  description = "Public Key Content"
}

variable "db_username" {
  sensitive = true
}
variable "db_password" {
  sensitive = true
}

#modificar esto en el eks
variable "admin_cidr" {
  description = "IP pública autorizada para acceder al endpoint de EKS"
  type        = string
}