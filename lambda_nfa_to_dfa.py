import sys
from utils import read_text_file, write_text_file

DEFAULT_INPUT_PATH = "data/lambda_nfa_to_dfa/input.txt"
DEFAULT_OUTPUT_PATH = "data/lambda_nfa_to_dfa/output.txt"
LAMBDA_SYMBOL = "λ"
LAMBDA_ALIASES = {"λ", "lambda", "eps", "epsilon", "ε"}


def normalize_symbol(symbol):
    if symbol.lower() in LAMBDA_ALIASES:
        return LAMBDA_SYMBOL
    return symbol


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
    transitions = {}
    for state in states:
        transitions[state] = {}

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

        if symbol not in transitions[from_state]:
            transitions[from_state][symbol] = set()
        transitions[from_state][symbol].add(to_state)

    initial_state = lines[3 + transition_count].strip()
    if initial_state not in state_set:
        raise ValueError("initial state does not exist: " + initial_state)

    final_states = lines[4 + transition_count].split()
    for final_state in final_states:
        if final_state not in state_set:
            raise ValueError("final state does not exist: " + final_state)

    return states, alphabet, transitions, initial_state, set(final_states)


def lambda_closure(state, transitions):
    closure = {state}
    stack = [state]

    while stack:
        current_state = stack.pop()
        next_states = transitions.get(current_state, {}).get(LAMBDA_SYMBOL, set())

        for next_state in next_states:
            if next_state not in closure:
                closure.add(next_state)
                stack.append(next_state)

    return closure


def lambda_closure_of_set(states_set, transitions):
    closure = set()

    for state in states_set:
        closure.update(lambda_closure(state, transitions))

    return closure


def subset_name(states_set):
    if not states_set:
        return "EMPTY"
    return "_".join(sorted(states_set))


def subset_sort_key(state_name, subsets):
    if state_name == "EMPTY":
        return (1, ())
    return (0, tuple(sorted(subsets.get(state_name, {state_name}))))


def minimal_state_sort_key(state_name):
    if state_name.startswith("M") and state_name[1:].isdigit():
        return int(state_name[1:])
    return 0


def build_dfa(states, alphabet, transitions, initial_state, final_states):
    start_subset = frozenset(lambda_closure(initial_state, transitions))
    start_name = subset_name(start_subset)

    dfa_states = [start_name]
    dfa_subsets = {start_name: start_subset}
    dfa_transitions = {}
    queue = [start_subset]
    seen_subsets = {start_subset}

    while queue:
        current_subset = queue.pop(0)
        current_name = subset_name(current_subset)
        dfa_transitions[current_name] = {}

        for symbol in alphabet:
            move_result = set()
            for state in current_subset:
                destinations = transitions.get(state, {}).get(symbol, set())
                move_result.update(destinations)

            next_subset = frozenset(lambda_closure_of_set(move_result, transitions))
            next_name = subset_name(next_subset)
            dfa_transitions[current_name][symbol] = next_name

            if next_subset not in seen_subsets:
                seen_subsets.add(next_subset)
                queue.append(next_subset)
                dfa_states.append(next_name)
                dfa_subsets[next_name] = next_subset

    dfa_final_states = set()
    for state_name, state_subset in dfa_subsets.items():
        if state_subset.intersection(final_states):
            dfa_final_states.add(state_name)

    return {
        "states": dfa_states,
        "alphabet": alphabet,
        "initial_state": start_name,
        "final_states": dfa_final_states,
        "transitions": dfa_transitions,
        "subsets": dfa_subsets,
    }


def complete_dfa(dfa):
    states = list(dfa["states"])
    alphabet = list(dfa["alphabet"])
    transitions = {}
    subsets = dict(dfa["subsets"])
    need_empty_state = False

    for state in states:
        transitions[state] = dict(dfa["transitions"].get(state, {}))
        for symbol in alphabet:
            if symbol not in transitions[state]:
                transitions[state][symbol] = "EMPTY"
                need_empty_state = True

    for state in states:
        for symbol in alphabet:
            if transitions[state][symbol] not in states:
                if transitions[state][symbol] == "EMPTY":
                    need_empty_state = True
                else:
                    states.append(transitions[state][symbol])
                    subsets[transitions[state][symbol]] = frozenset()

    if need_empty_state and "EMPTY" not in states:
        states.append("EMPTY")
        subsets["EMPTY"] = frozenset()

    if "EMPTY" in states:
        transitions["EMPTY"] = {}
        for symbol in alphabet:
            transitions["EMPTY"][symbol] = "EMPTY"
        if "EMPTY" not in subsets:
            subsets["EMPTY"] = frozenset()

    return {
        "states": states,
        "alphabet": alphabet,
        "initial_state": dfa["initial_state"],
        "final_states": set(dfa["final_states"]),
        "transitions": transitions,
        "subsets": subsets,
    }


def reachable_states(dfa):
    reached = {dfa["initial_state"]}
    queue = [dfa["initial_state"]]

    while queue:
        current_state = queue.pop(0)

        for symbol in dfa["alphabet"]:
            next_state = dfa["transitions"].get(current_state, {}).get(symbol)
            if next_state is not None and next_state not in reached:
                reached.add(next_state)
                queue.append(next_state)

    return reached


def group_index_for_state(state, partitions):
    for index, group in enumerate(partitions):
        if state in group:
            return index
    return -1


def minimize_dfa(dfa):
    reached = reachable_states(dfa)
    states = [state for state in dfa["states"] if state in reached]
    final_states = set(dfa["final_states"]).intersection(reached)
    non_final_states = set(states) - final_states

    partitions = []
    if final_states:
        partitions.append(final_states)
    if non_final_states:
        partitions.append(non_final_states)

    changed = True
    while changed:
        changed = False
        new_partitions = []

        for group in partitions:
            groups_by_signature = {}

            for state in sorted(group, key=lambda name: subset_sort_key(name, dfa["subsets"])):
                signature = []
                for symbol in dfa["alphabet"]:
                    destination = dfa["transitions"][state][symbol]
                    signature.append(group_index_for_state(destination, partitions))
                signature = tuple(signature)

                if signature not in groups_by_signature:
                    groups_by_signature[signature] = set()
                groups_by_signature[signature].add(state)

            if len(groups_by_signature) > 1:
                changed = True

            for signature in sorted(groups_by_signature):
                new_partitions.append(groups_by_signature[signature])

        partitions = new_partitions

    state_to_partition = {}
    for index, group in enumerate(partitions):
        for state in group:
            state_to_partition[state] = index

    start_partition = state_to_partition[dfa["initial_state"]]
    partition_transitions = {}
    for index, group in enumerate(partitions):
        representative = sorted(
            group, key=lambda name: subset_sort_key(name, dfa["subsets"])
        )[0]
        partition_transitions[index] = {}
        for symbol in dfa["alphabet"]:
            destination = dfa["transitions"][representative][symbol]
            partition_transitions[index][symbol] = state_to_partition[destination]

    partition_order = []
    seen_partitions = {start_partition}
    queue = [start_partition]

    while queue:
        current_partition = queue.pop(0)
        partition_order.append(current_partition)

        for symbol in dfa["alphabet"]:
            next_partition = partition_transitions[current_partition][symbol]
            if next_partition not in seen_partitions:
                seen_partitions.add(next_partition)
                queue.append(next_partition)

    for index in range(len(partitions)):
        if index not in seen_partitions:
            partition_order.append(index)

    partition_names = {}
    for index, partition_index in enumerate(partition_order):
        partition_names[partition_index] = "M" + str(index)

    minimal_states = [partition_names[index] for index in partition_order]
    minimal_initial_state = partition_names[start_partition]
    minimal_final_states = set()
    minimal_groups = {}
    minimal_transitions = {}

    for partition_index in partition_order:
        minimal_name = partition_names[partition_index]
        group = partitions[partition_index]
        minimal_groups[minimal_name] = sorted(
            group, key=lambda name: subset_sort_key(name, dfa["subsets"])
        )

        if group.intersection(final_states):
            minimal_final_states.add(minimal_name)

        minimal_transitions[minimal_name] = {}
        for symbol in dfa["alphabet"]:
            next_partition = partition_transitions[partition_index][symbol]
            minimal_transitions[minimal_name][symbol] = partition_names[next_partition]

    return {
        "states": minimal_states,
        "alphabet": dfa["alphabet"],
        "initial_state": minimal_initial_state,
        "final_states": minimal_final_states,
        "transitions": minimal_transitions,
        "groups": minimal_groups,
    }


def format_state_set(states):
    if not states:
        return "{}"
    return "{" + ",".join(sorted(states)) + "}"


def format_dfa_output(dfa, minimal_dfa):
    dfa_state_order = sorted(
        dfa["states"], key=lambda name: subset_sort_key(name, dfa["subsets"])
    )
    dfa_final_order = [
        state for state in dfa_state_order if state in dfa["final_states"]
    ]
    minimal_state_order = sorted(minimal_dfa["states"], key=minimal_state_sort_key)
    minimal_final_order = [
        state for state in minimal_state_order if state in minimal_dfa["final_states"]
    ]

    lines = []
    lines.append("====================")
    lines.append("DFA ECHIVALENT")
    lines.append("====================")
    lines.append("States:")
    lines.append(" ".join(dfa_state_order))
    lines.append("Alphabet:")
    lines.append(" ".join(dfa["alphabet"]))
    lines.append("Initial state:")
    lines.append(dfa["initial_state"])
    lines.append("Final states:")
    lines.append(" ".join(dfa_final_order))
    lines.append("State subsets:")
    for state in dfa_state_order:
        lines.append(state + " = " + format_state_set(dfa["subsets"][state]))
    lines.append("Transitions:")
    for state in dfa_state_order:
        for symbol in dfa["alphabet"]:
            destination = dfa["transitions"][state][symbol]
            lines.append(state + " " + destination + " " + symbol)

    lines.append("")
    lines.append("====================")
    lines.append("DFA MINIM")
    lines.append("====================")
    lines.append("States:")
    lines.append(" ".join(minimal_state_order))
    lines.append("Alphabet:")
    lines.append(" ".join(minimal_dfa["alphabet"]))
    lines.append("Initial state:")
    lines.append(minimal_dfa["initial_state"])
    lines.append("Final states:")
    lines.append(" ".join(minimal_final_order))
    lines.append("State groups:")
    for state in minimal_state_order:
        lines.append(state + " = " + " ".join(minimal_dfa["groups"][state]))
    lines.append("Transitions:")
    for state in minimal_state_order:
        for symbol in minimal_dfa["alphabet"]:
            destination = minimal_dfa["transitions"][state][symbol]
            lines.append(state + " " + destination + " " + symbol)

    return "\n".join(lines) + "\n"


def solve(input_text):
    try:
        states, alphabet, transitions, initial_state, final_states = parse_input(input_text)
        dfa = build_dfa(states, alphabet, transitions, initial_state, final_states)
        dfa = complete_dfa(dfa)
        minimal_dfa = minimize_dfa(dfa)
        return format_dfa_output(dfa, minimal_dfa)
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
        print("Usage: python3 lambda_nfa_to_dfa.py [input_path output_path]")
        return

    input_text = read_text_file(input_path)
    output_text = solve(input_text)
    write_text_file(output_path, output_text)


if __name__ == "__main__":
    main()
