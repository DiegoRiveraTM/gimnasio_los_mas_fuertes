resource "aws_security_group" "gym_lmf_sg_rds" {
  name        = "gym_lmf_sg_rds"
  description = "Private Security Group Rule for RDS / PostgreSQL"
  vpc_id      = aws_vpc.gym_lmf_vpc.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.eks.node_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "gym_lmf_sg_redis" {
  name        = "gym_lmf_sg_redis"
  description = "Private Security Group Rule for Redis"
  vpc_id      = aws_vpc.gym_lmf_vpc.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [module.eks.node_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "gym_lmf_sg_ec2" {
  name        = "gym_lmf_sg_ec2"
  description = "Instance Private SG"
  vpc_id      = aws_vpc.gym_lmf_vpc.id

  # No SSH inbound; SSM necesita conexión saliente por HTTPS (443).    
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}