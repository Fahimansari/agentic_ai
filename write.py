# sample.py

# Define the content you want to write to sample.js
js_content = """
// sample.js

console.log('Hello, World!');
"""

# Open (or create) the file in write mode
with open('sample.txt', 'w') as file:
    # Write the content to the file
    file.write(js_content)

print("sample.js file has been created and written to.")
