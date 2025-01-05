FROM public.ecr.aws/lambda/python:3.13 as builder

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM public.ecr.aws/lambda/python:3.13

# Copy only the necessary files from builder
COPY --from=builder /var/task/lib /var/task/lib

# Copy your application code
COPY web_scraper/main.py ./
COPY web_scraper/scrape.py ./
COPY web_scraper/parse.py ./

# Set the CMD to your handler
CMD [ "main.lambda_handler" ]