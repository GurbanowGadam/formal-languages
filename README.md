## Project Structure

```text
tema_2/
  lambda_nfa_to_dfa.py
  lambda_nfa_to_regex.py
  grammar_words.py
  regex_to_lambda_nfa.py
  utils.py
  README.md
  data/
    lambda_nfa_to_dfa/
      input.txt
      output.txt
    lambda_nfa_to_regex/
      input.txt
      output.txt
    grammar_words/
      input.txt
      output.txt
    regex_to_lambda_nfa/
      input.txt
      output.txt
```

## How to Run

Run with default input and output files:

```bash
python3 lambda_nfa_to_dfa.py
python3 lambda_nfa_to_regex.py
python3 grammar_words.py
python3 regex_to_lambda_nfa.py
```

## Lambda Notation

The programs accept these notations for lambda:

```text
λ, lambda, eps, epsilon, ε
```

Internally and in output files, the canonical symbol is:

```text
λ
```

## Part 1: λ-NFA to DFA

Script:

```bash
python3 lambda_nfa_to_dfa.py
```

Input format:

```text
states
alphabet
number_of_transitions
source destination symbol
...
initial_state
final_states
```

Example transition:

```text
q0 q1 λ
```

Output contains:

```text
DFA ECHIVALENT
DFA MINIM
```

The first section is the equivalent DFA. The second section is the minimized
DFA.

## Part 2: λ-NFA to Regular Expression

Script:

```bash
python3 lambda_nfa_to_regex.py
```

Input format is the same as for the λ-NFA to DFA script:

```text
states
alphabet
number_of_transitions
source destination symbol
...
initial_state
final_states
```

Output contains one equivalent regular expression:

```text
EXPRESIE REGULATA ECHIVALENTA
```

The empty regular expression is written as `∅`.

## Part 3: Grammar Words of Fixed Length

Script:

```bash
python3 grammar_words.py
```

Input format:

```text
nonterminals
terminals
number_of_productions
left_side right_side
...
start_symbol
word_length
```

Productions may be written compactly:

```text
S aA
```

or with spaces:

```text
S a A
```

Output contains all generated words of the requested length, one per line,
sorted lexicographically. If there is no word, the output is:

```text
NU EXISTA
```

If the generated word is empty and the requested length is `0`, the output is:

```text
λ
```

## Part 4: Regular Expression to λ-NFA

Script:

```bash
python3 regex_to_lambda_nfa.py
```

Input format:

```text
regular_expression
```

Supported syntax:

```text
|   union
*   Kleene star
( ) parentheses
```

Concatenation is implicit. For example:

```text
a(b|c)*
```

Output contains the equivalent λ-NFA:

```text
λ-NFA ECHIVALENT
```

with states, alphabet, initial state, final state, and transitions.
