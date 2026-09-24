resource "aws_vpc" "gym_lmf_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name        = "gym-lmf-vpc"
    Project     = "gym-lmf"
    Environment = "mvp"
  }
}

#Subnets públicas
resource "aws_subnet" "gym_lmf_subnet" {
  vpc_id            = aws_vpc.gym_lmf_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name                     = "gym-lmf-public-1a"
    Project                  = "gym-lmf"
    Environment              = "mvp"
    "kubernetes.io/role/elb" = "1"
  }
}

resource "aws_subnet" "gym_lmf_subnet_2" {
  vpc_id            = aws_vpc.gym_lmf_vpc.id
  cidr_block        = "10.0.4.0/24"
  availability_zone = "us-east-1b"

  tags = {
    Name                     = "gym-lmf-public-1b"
    Project                  = "gym-lmf"
    Environment              = "mvp"
    "kubernetes.io/role/elb" = "1"
  }
}

#Subnets privadas
resource "aws_subnet" "gym_lmf_private_subnet" {
  vpc_id            = aws_vpc.gym_lmf_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name                              = "gym-lmf-private-1a"
    Project                           = "gym-lmf"
    Environment                       = "mvp"
    "kubernetes.io/role/internal-elb" = "1"
  }
}

resource "aws_subnet" "gym_lmf_private_subnet_2" {
  vpc_id            = aws_vpc.gym_lmf_vpc.id
  cidr_block        = "10.0.3.0/24"
  availability_zone = "us-east-1b"

  tags = {
    Name                              = "gym-lmf-private-1b"
    Project                           = "gym-lmf"
    Environment                       = "mvp"
    "kubernetes.io/role/internal-elb" = "1"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "gym_lmf_igw" {
  vpc_id = aws_vpc.gym_lmf_vpc.id

  tags = {
    Name    = "gym-lmf-igw"
    Project = "gym-lmf"
  }
}

#Routing for public subnets
resource "aws_route_table" "gym_lmf_public_route_table" {
  vpc_id = aws_vpc.gym_lmf_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gym_lmf_igw.id
  }

  tags = {
    Name    = "gym-lmf-public-rt"
    Project = "gym-lmf"
  }
}

#One NAT Gateway
resource "aws_eip" "gym_lmf_nat_eip" {
  domain = "vpc"

  tags = {
    Name    = "gym-lmf-nat-eip"
    Project = "gym-lmf"
  }
}

resource "aws_nat_gateway" "gym_lmf_nat" {
  allocation_id = aws_eip.gym_lmf_nat_eip.id
  subnet_id     = aws_subnet.gym_lmf_subnet.id

  depends_on = [aws_internet_gateway.gym_lmf_igw]

  tags = {
    Name    = "gym-lmf-nat"
    Project = "gym-lmf"
  }
}

#Routing for private subnets
resource "aws_route_table" "gym_lmf_route_private_table" {
  vpc_id = aws_vpc.gym_lmf_vpc.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.gym_lmf_nat.id
  }

  tags = {
    Name    = "gym-lmf-private-rt"
    Project = "gym-lmf"
  }
}

#Public subnet associations
resource "aws_route_table_association" "public_1" {
  subnet_id      = aws_subnet.gym_lmf_subnet.id
  route_table_id = aws_route_table.gym_lmf_public_route_table.id
}

resource "aws_route_table_association" "public_2" {
  subnet_id      = aws_subnet.gym_lmf_subnet_2.id
  route_table_id = aws_route_table.gym_lmf_public_route_table.id
}

# Private subnet associations
resource "aws_route_table_association" "private_1" {
  subnet_id      = aws_subnet.gym_lmf_private_subnet.id
  route_table_id = aws_route_table.gym_lmf_route_private_table.id
}

resource "aws_route_table_association" "private_2" {
  subnet_id      = aws_subnet.gym_lmf_private_subnet_2.id
  route_table_id = aws_route_table.gym_lmf_route_private_table.id
}