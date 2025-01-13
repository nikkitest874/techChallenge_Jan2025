provider "aws" {
  region = "ca-central-1" # Set your AWS region
}

resource "aws_s3_bucket" "my_bucket" {
  bucket = "mybinance-gold-bucket" # Replace with your bucket name
  acl    = "private"               # Access control list (e.g., private, public-read)

  # Optional: Enable versioning
  versioning {
    enabled = true
  }

  # Optional: Enable server-side encryption
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256" # Use "AES256" or "aws:kms" for encryption
      }
    }
  }

  # Optional: Tags for resource management
  tags = {
    Name        = "mybinance-gold-bucket"
    Environment = "Production"
  }
}
