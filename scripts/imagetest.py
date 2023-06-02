import openai
openai.api_key = "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"
response = openai.Image.create(
  prompt="a white siamese cat",
  n=1,
  size="1024x1024"
)
image_url = response['data'][0]['url']

print(image_url)