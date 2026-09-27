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

  validation {
    condition = (
      can(cidrnetmask(var.admin_cidr)) &&
      can(regex("/32$", var.admin_cidr))
    )
    error_message = "admin_cidr debe ser una dirección IPv4 individual con máscara /32."
  }
}