import json
from datetime import datetime

import boto3
from parse import parse_with_cloud_llm
from scrape import (
    clean_body_content,
    extract_body_content,
    scrape_website,
    split_dom_content,
)

s3_client = boto3.client("s3")


def lambda_handler(event, context):
    try:
        # Get parameters from the event object
        parse_description = event.get("parse_description", "Wahlen 2025")
        url = event.get("url", "https://www.sueddeutsche.de/")
        max_length = event.get("max_length", 500)

        # scrape page
        dom_content = scrape_website(url)
        body_content = extract_body_content(dom_content)
        cleaned_content = clean_body_content(body_content)
        dom_chunks = split_dom_content(cleaned_content, max_length=max_length)

        parsed_result = parse_with_cloud_llm(dom_chunks, parse_description)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        s3_filename = f"test/parsed_result_{timestamp}.json"
        s3_client.put_object(
            Bucket=web_parser,
            Key=filename,
            Body=json.dumps(
                {
                    "parsed_result": parsed_result,
                }
            ),
            ContentType="application/json",
        )

        # Return the results in the required Lambda response format
        return {
            "statusCode": 200,
            "body": {
                "parsed_result": parsed_result,
                "url": url,
                "parse_description": parse_description,
            },
        }

    except Exception as e:
        # Error handling
        return {"statusCode": 500, "body": {"error": str(e)}}
