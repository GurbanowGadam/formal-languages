"""Convert a regular expression to a lambda-NFA.

This bonus script will read a regular expression and build an equivalent
lambda-NFA using Shunting Yard and Thompson construction.
"""

import sys
from utils import read_text_file, write_text_file


DEFAULT_INPUT_PATH = "data/regex_to_lambda_nfa/input.txt"
DEFAULT_OUTPUT_PATH = "data/regex_to_lambda_nfa/output.txt"
LAMBDA_SYMBOL = "λ"
LAMBDA_ALIASES = {"λ", "lambda", "eps", "epsilon", "ε"}
OPERATORS = {"|", "*", "."}


def normalize_symbol(symbol):
    if symbol.lower() in LAMBDA_ALIASES:
        return LAMBDA_SYMBOL
    return symbol


def is_lambda(symbol):
    return normalize_symbol(symbol) == LAMBDA_SYMBOL


def is_symbol(token):
    return token not in OPERATORS and token not in {"(", ")"}


def tokenize(regex):
    tokens = []
    index = 0

    while index < len(regex):
        character = regex[index]

        if character.isspace():
            index += 1
        elif character in {"|", "*", "(", ")"}:
            tokens.append(character)
            index += 1
        elif character in {"λ", "ε"}:
            tokens.append(LAMBDA_SYMBOL)
            index += 1
        elif character.isalnum() or character == "_":
            start = index
            while index < len(regex) and (
                regex[index].isalnum() or regex[index] == "_"
            ):
                index += 1

            word = regex[start:index]
            normalized_word = normalize_symbol(word)

            if normalized_word == LAMBDA_SYMBOL:
                tokens.append(LAMBDA_SYMBOL)
            elif "_" in word:
                tokens.append(word)
            else:
                for symbol in word:
                    tokens.append(symbol)
        else:
            raise ValueError("invalid character in regex: " + character)

    if not tokens:
        raise ValueError("the regular expression is empty")

    return tokens


def insert_concatenation(tokens):
    result = []

    for index, token in enumerate(tokens):
        if index > 0:
            previous = tokens[index - 1]
            left_can_end = is_symbol(previous) or previous == ")" or previous == "*"
            right_can_start = is_symbol(token) or token == "("

            if left_can_end and right_can_start:
                result.append(".")

        result.append(token)

    return result


def to_postfix(tokens):
    precedence = {"*": 3, ".": 2, "|": 1}
    output = []
    stack = []
    expecting_operand = True

    for token in tokens:
        if is_symbol(token):
            if not expecting_operand:
                raise ValueError("missing operator before symbol: " + token)
            output.append(token)
            expecting_operand = False
        elif token == "(":
            if not expecting_operand:
                raise ValueError("missing operator before '('")
            stack.append(token)
            expecting_operand = True
        elif token == ")":
            if expecting_operand:
                raise ValueError("invalid empty parentheses or operator before ')'")

            found_open_parenthesis = False
            while stack:
                top = stack.pop()
                if top == "(":
                    found_open_parenthesis = True
                    break
                output.append(top)

            if not found_open_parenthesis:
                raise ValueError("mismatched parentheses")

            expecting_operand = False
        elif token == "*":
            if expecting_operand:
                raise ValueError("invalid placement of '*'")
            output.append(token)
            expecting_operand = False
        elif token in {".", "|"}:
            if expecting_operand:
                raise ValueError("invalid placement of operator: " + token)

            while (
                stack
                and stack[-1] != "("
                and precedence[stack[-1]] >= precedence[token]
            ):
                output.append(stack.pop())

            stack.append(token)
            expecting_operand = True
        else:
            raise ValueError("unknown token: " + token)

    if expecting_operand:
        raise ValueError("the regular expression ends with an operator")

    while stack:
        top = stack.pop()
        if top == "(":
            raise ValueError("mismatched parentheses")
        output.append(top)

    return output


def build_thompson_nfa(postfix_tokens):
    states = []
    transitions = []
    alphabet = set()
    stack = []

    def new_state():
        state = "q" + str(len(states))
        states.append(state)
        return state

    def add_transition(from_state, to_state, symbol):
        transitions.append((from_state, to_state, symbol))

    for token in postfix_tokens:
        if is_symbol(token):
            start_state = new_state()
            final_state = new_state()
            add_transition(start_state, final_state, token)

            if token != LAMBDA_SYMBOL:
                alphabet.add(token)

            stack.append({"start": start_state, "final": final_state})

        elif token == ".":
            if len(stack) < 2:
                raise ValueError("not enough operands for concatenation")

            right_fragment = stack.pop()
            left_fragment = stack.pop()

            add_transition(
                left_fragment["final"], right_fragment["start"], LAMBDA_SYMBOL
            )

            stack.append(
                {
                    "start": left_fragment["start"],
                    "final": right_fragment["final"],
                }
            )

        elif token == "|":
            if len(stack) < 2:
                raise ValueError("not enough operands for union")

            right_fragment = stack.pop()
            left_fragment = stack.pop()
            start_state = new_state()
            final_state = new_state()

            add_transition(start_state, left_fragment["start"], LAMBDA_SYMBOL)
            add_transition(start_state, right_fragment["start"], LAMBDA_SYMBOL)
            add_transition(left_fragment["final"], final_state, LAMBDA_SYMBOL)
            add_transition(right_fragment["final"], final_state, LAMBDA_SYMBOL)

            stack.append({"start": start_state, "final": final_state})

        elif token == "*":
            if len(stack) < 1:
                raise ValueError("not enough operands for Kleene star")

            fragment = stack.pop()
            start_state = new_state()
            final_state = new_state()

            add_transition(start_state, fragment["start"], LAMBDA_SYMBOL)
            add_transition(start_state, final_state, LAMBDA_SYMBOL)
            add_transition(fragment["final"], fragment["start"], LAMBDA_SYMBOL)
            add_transition(fragment["final"], final_state, LAMBDA_SYMBOL)

            stack.append({"start": start_state, "final": final_state})

    if len(stack) != 1:
        raise ValueError("invalid regular expression")

    final_fragment = stack[0]

    return {
        "states": states,
        "alphabet": sorted(alphabet),
        "initial_state": final_fragment["start"],
        "final_state": final_fragment["final"],
        "transitions": transitions,
    }


def format_output(nfa):
    lines = []
    lines.append("====================")
    lines.append("λ-NFA ECHIVALENT")
    lines.append("====================")
    lines.append("States:")
    lines.append(" ".join(nfa["states"]))
    lines.append("Alphabet:")
    lines.append(" ".join(nfa["alphabet"]))
    lines.append("Initial state:")
    lines.append(nfa["initial_state"])
    lines.append("Final state:")
    lines.append(nfa["final_state"])
    lines.append("Transitions:")

    for from_state, to_state, symbol in nfa["transitions"]:
        lines.append(from_state + " " + to_state + " " + symbol)

    return "\n".join(lines) + "\n"


def solve(input_text):
    try:
        regex = input_text.strip()
        tokens = tokenize(regex)
        tokens_with_concatenation = insert_concatenation(tokens)
        postfix_tokens = to_postfix(tokens_with_concatenation)
        nfa = build_thompson_nfa(postfix_tokens)
        return format_output(nfa)
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
        print("Usage: python3 regex_to_lambda_nfa.py [input_path output_path]")
        return

    input_text = read_text_file(input_path)
    output_text = solve(input_text)
    write_text_file(output_path, output_text)


if __name__ == "__main__":
    main()
