resource "aws_iam_role" "gym_lmf_role" {
  name = "gym-lmf-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "gym_lmf_ssm" {
  role       = aws_iam_role.gym_lmf_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "gym_lmf_profile" {
  name = "gym-lmf-instance-profile"
  role = aws_iam_role.gym_lmf_role.name
}