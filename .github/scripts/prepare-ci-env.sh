#!/usr/bin/env bash
set -euo pipefail

cp env.example .env
sed -i.bak 's/^OPENAI_API_KEY=.*/OPENAI_API_KEY=ci-dummy-key/' .env
sed -i.bak 's|^S3_ENDPOINT=.*|S3_ENDPOINT=http://localhost:9000|' .env
sed -i.bak 's/^S3_ACCESS_KEY=.*/S3_ACCESS_KEY=ci-dummy-key/' .env
sed -i.bak 's/^S3_SECRET_KEY=.*/S3_SECRET_KEY=ci-dummy-secret/' .env
sed -i.bak 's/^S3_REGION_NAME=.*/S3_REGION_NAME=eu-central-1/' .env
rm .env.bak
