from llama_cpp import Llama
import pathlib



template = (
    "You are tasked with summarizing information from the following news content: {dom_content}. "
)

llama_path=pathlib.Path(__file__).parents[1] / "llama-cpp/models/llama-3-70B/Meta-Llama-3-70B-Instruct-IQ2_XS.gguf"
zephyr_path=pathlib.Path(__file__).parents[1] / "llama-cpp/models/zephyr-7b-beta.Q4_0.gguf"

model = Llama(
      model_path=str(zephyr_path),
      n_gpu_layers=-1, # Uncomment to use GPU acceleration
      # seed=1337, # Uncomment to set a specific seed
      # n_ctx=2048, # Uncomment to increase the context window
)


def parse_with_llama_local(dom_chunks, parse_description):
    parsed_results = []
    for i, chunk in enumerate(dom_chunks, start=1):
        print(f"Parsing batch: {i} of {len(dom_chunks)}")
        prompt = template.format(dom_content=chunk)#, parse_description=parse_description)
        response = model(prompt, max_tokens=100) # many options here 
        print(f"Parsed batch: {response}")
        parsed_results.append(response)

    return "\n".join(parsed_results)