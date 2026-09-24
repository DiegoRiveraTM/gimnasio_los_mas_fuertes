module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "21.25.0"

  name               = "gym-lmf"
  kubernetes_version = "1.36"

  vpc_id = aws_vpc.gym_lmf_vpc.id

  subnet_ids = [
    aws_subnet.gym_lmf_private_subnet.id,
    aws_subnet.gym_lmf_private_subnet_2.id,
  ]

  endpoint_private_access = true
  endpoint_public_access  = true

  #Limítalo a tu IP pública; actualízala al cambiar de casa a la escuela.
  endpoint_public_access_cidrs = [var.admin_cidr]

  enable_cluster_creator_admin_permissions = true

  tags = {
    Environment = "dev"
    Terraform   = "true"
  }
}