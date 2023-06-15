import os
import openai
openai.api_key = ""
models = openai.Model.list()

root_values = [model['root'] for model in models['data']]
print(root_values)
