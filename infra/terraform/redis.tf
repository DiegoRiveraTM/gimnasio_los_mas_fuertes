resource "aws_elasticache_subnet_group" "gym_lmf" {
  name = "gym-lmf-redis-subnet"
  subnet_ids = [
    aws_subnet.gym_lmf_private_subnet.id,
    aws_subnet.gym_lmf_private_subnet_2.id,
  ]
}

resource "aws_elasticache_cluster" "gym_lmf" {
  cluster_id           = "cluster-gym-lmf"
  engine               = "redis"
  engine_version       = "7.1"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379

  security_group_ids = [
    aws_security_group.gym_lmf_sg_redis.id,
  ]

  subnet_group_name = aws_elasticache_subnet_group.gym_lmf.name
}