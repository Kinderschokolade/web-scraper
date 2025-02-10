import os
import pathlib
from dotenv import load_dotenv
from llama_cpp import Llama
from openai import OpenAI

template = "You are tasked with summarizing information from the following news content: {dom_content}. "

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_TOKEN"))

def create_prompt(chunk):
    return template.format(dom_content=chunk)

def parse_with_cloud_llm(dom_chunks, parse_description):
    return parse_with_llm(dom_chunks, parse_description, use_cloud=True)

def parse_with_local_llm(dom_chunks, parse_description):
    return parse_with_llm(dom_chunks, parse_description, use_cloud=False)

def parse_with_llm(dom_chunks, parse_description, use_cloud):
    parsed_results = []
    for i, chunk in enumerate(dom_chunks, start=1):
        print(f"Parsing batch: {i} of {len(dom_chunks)}")
        prompt = create_prompt(chunk)
        response = get_llm_response(prompt, use_cloud)
        print(f"Parsed batch: {response}")
        parsed_results.append(response)
    return "\n".join(parsed_results)

def get_llm_response(prompt, use_cloud):
    if use_cloud:
        response = (
            openai_client.chat.completions.create(
                model="gpt-4o-mini",
                store=False,
                messages=[{"role": "user", "content": prompt}],
            )
            .choices[0]
            .message
        )
    else:
        zephyr_path = (
            pathlib.Path(__file__).parents[1] / "llama-cpp/models/zephyr-7b-beta.Q4_0.gguf"
        )
        model = Llama(
            model_path=str(zephyr_path),
            n_gpu_layers=-1,
        )
        response = model(prompt, max_tokens=100)
    return response
