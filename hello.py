from transformers import PegasusForConditionalGeneration, PegasusTokenizer
import torch

def test_pegasus_model():
    model_name = "google/pegasus-cnn_dailymail"
    tokenizer = PegasusTokenizer.from_pretrained(model_name)
    model = PegasusForConditionalGeneration.from_pretrained(model_name)

    # Example test input
    text = "Artificial Intelligence is transforming industries, automating tasks, and improving efficiency."

    # Prepare inputs and generate the summary
    inputs = tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)
    summary_ids = model.generate(inputs["input_ids"], max_length=150, num_beams=5, early_stopping=True)

    # Decode and print the summary
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    print(summary)

test_pegasus_model()
