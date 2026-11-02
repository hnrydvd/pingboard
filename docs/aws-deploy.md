# AWS deploy notes (Phase 2)

Do it by hand in the console first and write down every step here. Later in Phase 2 (Feb–Mar) this file becomes the spec for the Terraform code.

**Before anything else:** set a billing alarm (Billing → Budgets, e.g. $20/month, email alert).

## Checklist

- [ ] IAM: admin user with MFA, stop using root
- [ ] VPC: 2 public subnets in different AZs (the ALB needs two)
- [ ] Security groups: ALB allows 80/443 from the internet; EC2 allows 8080 from the ALB SG only, 22 from my IP only
- [ ] EC2: small instance, install Docker + Compose, `docker compose up -d`
- [ ] ALB: target group → EC2:8080, health check path `/` (later: `/api/healthz` via nginx)
- [ ] Route53: `pingboard.<my-domain>` → ALB alias record
- [ ] ACM cert on the ALB for HTTPS
- [ ] S3 bucket + instance role (not access keys!) allowing `s3:PutObject`; cron `pg_dump | gzip | aws s3 cp - s3://...`
- [ ] Teardown steps written down, and actually tested

## Steps taken

_Fill in as you go._

## Costs observed

_Fill in from Cost Explorer._
