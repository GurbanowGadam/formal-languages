from collections import deque
import sys
from utils import read_text_file, write_text_file

DEFAULT_INPUT_PATH = "data/grammar_words/input.txt"
DEFAULT_OUTPUT_PATH = "data/grammar_words/output.txt"
LAMBDA_SYMBOL = "λ"
LAMBDA_ALIASES = {"λ", "lambda", "eps", "epsilon", "ε"}
INFINITY = 10**9


def normalize_symbol(symbol):
    if symbol.lower() in LAMBDA_ALIASES:
        return LAMBDA_SYMBOL
    return symbol


def is_lambda(symbol):
    return normalize_symbol(symbol) == LAMBDA_SYMBOL


def split_compact_symbols(text, known_symbols):
    result = []
    position = 0
    ordered_symbols = sorted(known_symbols, key=len, reverse=True)

    while position < len(text):
        matched_symbol = None

        for symbol in ordered_symbols:
            if text.startswith(symbol, position):
                matched_symbol = symbol
                break

        if matched_symbol is None:
            raise ValueError("unknown symbol in production right side: " + text)

        result.append(matched_symbol)
        position += len(matched_symbol)

    return result


def parse_right_side(tokens, known_symbols):
    if len(tokens) == 1 and is_lambda(tokens[0]):
        return tuple()

    right_side = []
    for token in tokens:
        normalized_token = normalize_symbol(token)

        if normalized_token == LAMBDA_SYMBOL:
            raise ValueError("lambda must be alone on a production right side")
        if normalized_token in known_symbols:
            right_side.append(normalized_token)
        else:
            right_side.extend(split_compact_symbols(normalized_token, known_symbols))

    return tuple(right_side)


def parse_input(input_text):
    lines = [line.strip() for line in input_text.splitlines()]

    if len(lines) < 5:
        raise ValueError("missing lines in input")

    nonterminals = lines[0].split()
    terminals = lines[1].split()

    if not nonterminals:
        raise ValueError("the list of nonterminals is missing")

    terminals = [normalize_symbol(symbol) for symbol in terminals]
    if LAMBDA_SYMBOL in terminals:
        raise ValueError("lambda cannot be a terminal symbol")

    try:
        production_count = int(lines[2])
    except ValueError:
        raise ValueError("the number of productions must be an integer")

    if production_count < 0:
        raise ValueError("the number of productions cannot be negative")

    expected_line_count = 3 + production_count + 2
    if len(lines) < expected_line_count:
        raise ValueError("missing lines after the production list")

    nonterminal_set = set(nonterminals)
    terminal_set = set(terminals)
    known_symbols = list(nonterminals) + list(terminals)
    productions = {}
    for nonterminal in nonterminals:
        productions[nonterminal] = []

    for index in range(production_count):
        line_number = 4 + index
        tokens = lines[3 + index].split()

        if len(tokens) < 2:
            raise ValueError(
                "production line "
                + str(line_number)
                + " must have at least 2 tokens"
            )

        left_side = tokens[0]
        if left_side not in nonterminal_set:
            raise ValueError("production left side is not a nonterminal: " + left_side)

        right_side = parse_right_side(tokens[1:], known_symbols)
        for symbol in right_side:
            if symbol not in nonterminal_set and symbol not in terminal_set:
                raise ValueError("unknown symbol in production: " + symbol)

        productions[left_side].append(right_side)

    start_symbol = lines[3 + production_count].strip()
    if start_symbol not in nonterminal_set:
        raise ValueError("start symbol is not a nonterminal: " + start_symbol)

    try:
        word_length = int(lines[4 + production_count])
    except ValueError:
        raise ValueError("X must be a non-negative integer")

    if word_length < 0:
        raise ValueError("X must be a non-negative integer")

    return {
        "nonterminals": nonterminals,
        "terminals": terminals,
        "productions": productions,
        "start_symbol": start_symbol,
        "word_length": word_length,
    }


def compute_min_lengths(nonterminals, terminals, productions):
    terminal_set = set(terminals)
    nonterminal_set = set(nonterminals)
    min_lengths = {}

    for nonterminal in nonterminals:
        min_lengths[nonterminal] = INFINITY

    changed = True
    while changed:
        changed = False

        for nonterminal in nonterminals:
            for right_side in productions[nonterminal]:
                length = 0
                possible = True

                for symbol in right_side:
                    if symbol in terminal_set:
                        length += 1
                    elif symbol in nonterminal_set:
                        if min_lengths[symbol] == INFINITY:
                            possible = False
                            break
                        length += min_lengths[symbol]

                if possible and length < min_lengths[nonterminal]:
                    min_lengths[nonterminal] = length
                    changed = True

    return min_lengths


def terminal_count(form, terminals):
    terminal_set = set(terminals)
    count = 0

    for symbol in form:
        if symbol in terminal_set:
            count += 1

    return count


def minimum_possible_length(form, terminals, min_lengths):
    terminal_set = set(terminals)
    total_length = 0

    for symbol in form:
        if symbol in terminal_set:
            total_length += 1
        elif symbol in min_lengths:
            if min_lengths[symbol] == INFINITY:
                return INFINITY
            total_length += min_lengths[symbol]

    return total_length


def contains_nonterminal(form, nonterminals):
    nonterminal_set = set(nonterminals)

    for symbol in form:
        if symbol in nonterminal_set:
            return True

    return False


def first_nonterminal_index(form, nonterminals):
    nonterminal_set = set(nonterminals)

    for index, symbol in enumerate(form):
        if symbol in nonterminal_set:
            return index

    return -1


def is_promising_form(form, grammar_data, min_lengths, max_form_symbols):
    terminals = grammar_data["terminals"]
    word_length = grammar_data["word_length"]

    if terminal_count(form, terminals) > word_length:
        return False

    if minimum_possible_length(form, terminals, min_lengths) > word_length:
        return False

    if len(form) > max_form_symbols:
        return False

    return True


def generate_words(grammar_data):
    nonterminals = grammar_data["nonterminals"]
    terminals = grammar_data["terminals"]
    productions = grammar_data["productions"]
    start_symbol = grammar_data["start_symbol"]
    word_length = grammar_data["word_length"]

    min_lengths = compute_min_lengths(nonterminals, terminals, productions)
    max_form_symbols = word_length + len(nonterminals) + 5

    start_form = (start_symbol,)
    queue = deque([start_form])
    seen_forms = {start_form}
    result_words = set()

    while queue:
        form = queue.popleft()

        if not is_promising_form(form, grammar_data, min_lengths, max_form_symbols):
            continue

        if not contains_nonterminal(form, nonterminals):
            if terminal_count(form, terminals) == word_length:
                if word_length == 0:
                    result_words.add(LAMBDA_SYMBOL)
                else:
                    result_words.add("".join(form))
            continue

        index = first_nonterminal_index(form, nonterminals)
        nonterminal = form[index]

        for right_side in productions[nonterminal]:
            new_form = form[:index] + right_side + form[index + 1 :]

            if new_form in seen_forms:
                continue

            seen_forms.add(new_form)

            if is_promising_form(new_form, grammar_data, min_lengths, max_form_symbols):
                queue.append(new_form)

    return sorted(result_words)


def solve(input_text):
    try:
        grammar_data = parse_input(input_text)
        words = generate_words(grammar_data)

        if not words:
            return "NU EXISTA\n"

        return "\n".join(words) + "\n"
    except ValueError as error:
        return "Error: " + str(error) + "\n"


def main():
    if len(sys.argv) == 1:
        input_path = DEFAULT_INPUT_PATH
        output_path = DEFAULT_OUTPUT_PATH
    elif len(sys.argv) == 3:
        input_path = sys.argv[1]
        output_path = sys.argv[2]
    else:
        print("Usage: python3 grammar_words.py [input_path output_path]")
        return

    input_text = read_text_file(input_path)
    output_text = solve(input_text)
    write_text_file(output_path, output_text)

if __name__ == "__main__":
    main()
