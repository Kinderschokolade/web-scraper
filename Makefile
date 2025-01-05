
requirements: 
	poetry export --without-hashes --format=requirements.txt > requirements.txt

build_env:
	poetry install --with local

activate_env:
	source .venv/bin/activate

build_docker:
	make requirements
	docker build -t web-scraper-lambda .

push_docker:
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
	docker tag web-scraper-lambda:latest $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/web-scraper-lambda:latest
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/web-scraper-lambda:latest

test:
	.

test_docker:
	.

run_docker:
	.