resource "aws_db_subnet_group" "gym_lmf" {
  name = "gym-lmf-rds-subnet"

  subnet_ids = [
    aws_subnet.gym_lmf_private_subnet.id,
    aws_subnet.gym_lmf_private_subnet_2.id,
  ]
}

resource "aws_db_instance" "gym_lmf" {
  identifier          = "gym-lmf-postgres"
  allocated_storage   = 20
  storage_type        = "gp3"
  db_name             = "gym_lmf_db"
  engine              = "postgres"
  engine_version      = "16.15"
  instance_class      = "db.t3.micro"
  username            = var.db_username
  password            = var.db_password
  parameter_group_name = "default.postgres16"

  db_subnet_group_name   = aws_db_subnet_group.gym_lmf.name
  vpc_security_group_ids = [aws_security_group.gym_lmf_sg_rds.id]
  publicly_accessible    = false

  skip_final_snapshot = true
}