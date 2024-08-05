from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("sunithalv/MedPaxTral-2x7b_2")
model = AutoModelForCausalLM.from_pretrained("sunithalv/MedPaxTral-2x7b_2", ignore_mismatched_sizes=True)

# Example usage with task prefix
input_text = "question: What are the symptoms of ADRD?"
input_ids = tokenizer.encode(input_text, return_tensors="pt")
outputs = model.generate(input_ids, max_new_tokens=50)

# Decode the output tokens to text
decoded_output = tokenizer.decode(outputs[0], skip_special_tokens=True)

print(decoded_output)
