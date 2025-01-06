import os
import pathlib
from dotenv import load_dotenv
from llama_cpp import Llama
from openai import OpenAI

template = "You are tasked with summarizing information from the following news content: {dom_content}. "


load_dotenv()

openai_client = OpenAI(
    api_key=os.getenv("OPENAI_TOKEN"),
)


def parse_with_cloud_llm(dom_chunks, parse_description):
    parsed_results = []
    for i, chunk in enumerate(dom_chunks, start=1):
        print(f"Parsing batch: {i} of {len(dom_chunks)}")
        prompt = template.format(dom_content=chunk)
        response = (
            openai_client.chat.completions.create(
                model="gpt-4o-mini",
                store=False,
                messages=[{"role": "user", "content": prompt}],
            )
            .choices[0]
            .message
        )

        print(f"Parsed batch: {response}")
        parsed_results.append(response)

    return "\n".join(parsed_results)


def parse_with_local_llm(dom_chunks, parse_description):
    llama_path = (
        pathlib.Path(__file__).parents[1]
        / "llama-cpp/models/llama-3-70B/Meta-Llama-3-70B-Instruct-IQ2_XS.gguf"
    )
    zephyr_path = (
        pathlib.Path(__file__).parents[1] / "llama-cpp/models/zephyr-7b-beta.Q4_0.gguf"
    )

    model = Llama(
        model_path=str(zephyr_path),
        n_gpu_layers=-1,  # use GPU acceleration
        # seed=1337, # Uncomment to set a specific seed
        # n_ctx=2048, # Uncomment to increase the context window
    )
    parsed_results = []
    for i, chunk in enumerate(dom_chunks, start=1):
        print(f"Parsing batch: {i} of {len(dom_chunks)}")
        prompt = template.format(
            dom_content=chunk
        )  # , parse_description=parse_description)
        response = model(prompt, max_tokens=100)  # many options here
        print(f"Parsed batch: {response}")
        parsed_results.append(response)

    return "\n".join(parsed_results)
