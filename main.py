from scrape import (
    scrape_website,
    extract_body_content,
    clean_body_content,
    split_dom_content,
)
from parse import parse_with_llm 


if __name__=="__main__":
    parse_description = "Wahlen 2025"
    url = "https://www.sueddeutsche.de/"
    #dom_content = scrape_website(url)
    #body_content = extract_body_content(dom_content)
    #cleaned_content = clean_body_content(body_content)
    #with open("save.txt", "w") as text_file:
    #    text_file.write(cleaned_content)

    with open("save.txt", "r") as text_file:
        cleaned_content =  text_file.read()
    
    dom_chunks = split_dom_content(cleaned_content,max_length=500)
    
    parsed_result = parse_with_llm(dom_chunks, parse_description)
    print(parsed_result)