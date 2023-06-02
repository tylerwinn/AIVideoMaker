import os
import openai
openai.api_key = "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"
models = openai.Model.list()

root_values = [model['root'] for model in models['data']]
print(root_values)