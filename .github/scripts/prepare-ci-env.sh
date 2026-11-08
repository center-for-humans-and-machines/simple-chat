#!/usr/bin/env bash
set -euo pipefail

cp backend/env.example backend/.env
sed -i 's/^OPENAI_API_KEY=.*/OPENAI_API_KEY=ci-dummy-key/' backend/.env
sed -i 's|^S3_ENDPOINT=.*|S3_ENDPOINT=http://localhost:9000|' backend/.env
sed -i 's/^S3_ACCESS_KEY=.*/S3_ACCESS_KEY=ci-dummy-key/' backend/.env
sed -i 's/^S3_SECRET_KEY=.*/S3_SECRET_KEY=ci-dummy-secret/' backend/.env
sed -i 's/^S3_REGION_NAME=.*/S3_REGION_NAME=eu-central-1/' backend/.env
