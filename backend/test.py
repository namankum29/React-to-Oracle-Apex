from generator.apex_generator import generate_apex_page

with open("test_react.jsx", "r") as f:
    code = f.read()

sql = generate_apex_page(code)

print(sql)