def read_text_file(path):
    with open(path, "r", encoding="utf-8") as input_file:
        return input_file.read()


def write_text_file(path, content):
    with open(path, "w", encoding="utf-8") as output_file:
        output_file.write(content)
