"""Convert a lambda-NFA to a regular expression.

This script will read a lambda-NFA and compute an equivalent regular
expression using the state elimination method.
"""

import sys
from utils import read_text_file, write_text_file


DEFAULT_INPUT_PATH = "data/lambda_nfa_to_regex/input.txt"
DEFAULT_OUTPUT_PATH = "data/lambda_nfa_to_regex/output.txt"
LAMBDA_SYMBOL = "λ"
EMPTY_REGEX = "∅"
NEW_START_STATE = "__START__"
NEW_FINAL_STATE = "__FINAL__"
LAMBDA_ALIASES = {"λ", "lambda", "eps", "epsilon", "ε"}


def normalize_symbol(symbol):
    if symbol.lower() in LAMBDA_ALIASES:
        return LAMBDA_SYMBOL
    return symbol


def is_lambda(symbol):
    return normalize_symbol(symbol) == LAMBDA_SYMBOL


def parse_input(input_text):
    lines = [line.strip() for line in input_text.splitlines()]

    if len(lines) < 5:
        raise ValueError("missing lines in input")

    states = lines[0].split()
    if not states:
        raise ValueError("the list of states is missing")

    alphabet = []
    for symbol in lines[1].split():
        normalized_symbol = normalize_symbol(symbol)
        if normalized_symbol != LAMBDA_SYMBOL and normalized_symbol not in alphabet:
            alphabet.append(normalized_symbol)

    try:
        transition_count = int(lines[2])
    except ValueError:
        raise ValueError("the number of transitions must be an integer")

    if transition_count < 0:
        raise ValueError("the number of transitions cannot be negative")

    expected_line_count = 3 + transition_count + 2
    if len(lines) < expected_line_count:
        raise ValueError("missing lines after the transition list")

    state_set = set(states)
    transitions = []

    for index in range(transition_count):
        line_number = 4 + index
        tokens = lines[3 + index].split()

        if len(tokens) != 3:
            raise ValueError(
                "transition line "
                + str(line_number)
                + " must have exactly 3 tokens"
            )

        from_state, to_state, symbol = tokens
        symbol = normalize_symbol(symbol)

        if from_state not in state_set:
            raise ValueError("unknown transition source state: " + from_state)
        if to_state not in state_set:
            raise ValueError("unknown transition destination state: " + to_state)
        if symbol != LAMBDA_SYMBOL and symbol not in alphabet:
            raise ValueError("transition symbol is not in the alphabet: " + symbol)

        transitions.append((from_state, to_state, symbol))

    initial_state = lines[3 + transition_count].strip()
    if initial_state not in state_set:
        raise ValueError("initial state does not exist: " + initial_state)

    final_states = lines[4 + transition_count].split()
    for final_state in final_states:
        if final_state not in state_set:
            raise ValueError("final state does not exist: " + final_state)

    return {
        "states": states,
        "alphabet": alphabet,
        "transitions": transitions,
        "initial_state": initial_state,
        "final_states": final_states,
    }


def split_top_level_union(regex):
    parts = []
    start = 0
    depth = 0

    for index, character in enumerate(regex):
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
        elif character == "|" and depth == 0:
            parts.append(regex[start:index])
            start = index + 1

    parts.append(regex[start:])
    return parts


def regex_union(a, b):
    if a == EMPTY_REGEX:
        return b
    if b == EMPTY_REGEX:
        return a
    if a == b:
        return a

    parts = []
    seen_parts = set()
    for regex in split_top_level_union(a) + split_top_level_union(b):
        if regex not in seen_parts:
            parts.append(regex)
            seen_parts.add(regex)

    return "|".join(parts)


def needs_parentheses_for_concat(regex):
    if regex in (EMPTY_REGEX, LAMBDA_SYMBOL):
        return False

    depth = 0
    for character in regex:
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
        elif character == "|" and depth == 0:
            return True

    return False


def needs_parentheses_for_star(regex):
    if regex in (EMPTY_REGEX, LAMBDA_SYMBOL):
        return False

    if len(regex) == 1:
        return False

    if regex.endswith("*") and not needs_parentheses_for_concat(regex[:-1]):
        return False

    return True


def parenthesize_for_concat(regex):
    if needs_parentheses_for_concat(regex):
        return "(" + regex + ")"
    return regex


def regex_concat(a, b):
    if a == EMPTY_REGEX or b == EMPTY_REGEX:
        return EMPTY_REGEX
    if a == LAMBDA_SYMBOL:
        return b
    if b == LAMBDA_SYMBOL:
        return a

    return parenthesize_for_concat(a) + parenthesize_for_concat(b)


def regex_star(a):
    if a == EMPTY_REGEX or a == LAMBDA_SYMBOL:
        return LAMBDA_SYMBOL
    if a.endswith("*") and not needs_parentheses_for_star(a[:-1]):
        return a
    if needs_parentheses_for_star(a):
        return "(" + a + ")*"
    return a + "*"


def add_regex_edge(edges, from_state, to_state, label):
    key = (from_state, to_state)
    old_label = edges.get(key, EMPTY_REGEX)
    edges[key] = regex_union(old_label, label)


def build_gnfa(data):
    states = [NEW_START_STATE] + list(data["states"]) + [NEW_FINAL_STATE]
    edges = {}

    add_regex_edge(edges, NEW_START_STATE, data["initial_state"], LAMBDA_SYMBOL)

    for from_state, to_state, symbol in data["transitions"]:
        add_regex_edge(edges, from_state, to_state, symbol)

    for final_state in data["final_states"]:
        add_regex_edge(edges, final_state, NEW_FINAL_STATE, LAMBDA_SYMBOL)

    return states, edges


def get_edge_label(edges, from_state, to_state):
    return edges.get((from_state, to_state), EMPTY_REGEX)


def eliminate_state(edges, states, state_to_remove):
    remaining_states = []
    for state in states:
        if state != state_to_remove:
            remaining_states.append(state)

    loop_label = get_edge_label(edges, state_to_remove, state_to_remove)
    loop_star = regex_star(loop_label)

    for from_state in remaining_states:
        for to_state in remaining_states:
            direct_label = get_edge_label(edges, from_state, to_state)
            first_part = get_edge_label(edges, from_state, state_to_remove)
            last_part = get_edge_label(edges, state_to_remove, to_state)

            through_removed = regex_concat(regex_concat(first_part, loop_star), last_part)
            new_label = regex_union(direct_label, through_removed)

            if new_label == EMPTY_REGEX:
                edges.pop((from_state, to_state), None)
            else:
                edges[(from_state, to_state)] = new_label

    keys_to_remove = []
    for from_state, to_state in edges:
        if from_state == state_to_remove or to_state == state_to_remove:
            keys_to_remove.append((from_state, to_state))

    for key in keys_to_remove:
        edges.pop(key, None)

    return remaining_states


def nfa_to_regex(data):
    states, edges = build_gnfa(data)

    for state in data["states"]:
        states = eliminate_state(edges, states, state)

    return get_edge_label(edges, NEW_START_STATE, NEW_FINAL_STATE)


def solve(input_text):
    try:
        data = parse_input(input_text)
        regular_expression = nfa_to_regex(data)

        return (
            "====================\n"
            "EXPRESIE REGULATA ECHIVALENTA\n"
            "====================\n"
            + regular_expression
            + "\n"
        )
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
        print("Usage: python3 lambda_nfa_to_regex.py [input_path output_path]")
        return

    input_text = read_text_file(input_path)
    output_text = solve(input_text)
    write_text_file(output_path, output_text)


if __name__ == "__main__":
    main()
