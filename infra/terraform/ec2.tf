data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
  owners = ["099720109477"]
}

resource "aws_instance" "gym_lmf_Instance" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t3.micro"
  subnet_id              = aws_subnet.gym_lmf_private_subnet.id
  vpc_security_group_ids = [aws_security_group.gym_lmf_sg_ec2.id]
  key_name               = aws_key_pair.gym_lmf.key_name
  iam_instance_profile   = aws_iam_instance_profile.gym_lmf_profile.name

  tags = {
    Name = "TaskForMe-Instance"
  }
}

resource "aws_key_pair" "gym_lmf" {
  key_name   = "gym-lmf-key"
  public_key = file(var.public_key_path)
}

module "eks_managed_node_group" {
  source  = "terraform-aws-modules/eks/aws//modules/eks-managed-node-group"
  version = "21.25.0"

  name         = "gym-lmf-nodes"
  cluster_name = module.eks.cluster_name

  kubernetes_version = "1.36"

  subnet_ids = [
    aws_subnet.gym_lmf_private_subnet.id,
    aws_subnet.gym_lmf_private_subnet_2.id,
  ]

  cluster_primary_security_group_id = module.eks.cluster_primary_security_group_id
  vpc_security_group_ids            = [module.eks.node_security_group_id]

  min_size     = 1
  max_size     = 2
  desired_size = 1

  instance_types = ["t3.medium"]
  capacity_type  = "ON_DEMAND"

  tags = {
    Environment = "dev"
    Terraform   = "true"
  }
}