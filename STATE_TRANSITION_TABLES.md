# Theory of Computation — PDA State Transition Tables
**Project:** Applications of Pushdown Automata (PDA)  
**Presented by:** Group 6 (Roll Nos. 61–69), Comp C  
**Subject:** Theory of Computation (TOC)  

---

## General Definition of a Pushdown Automaton (PDA)

In formal language theory, a Pushdown Automaton is formally defined as a 7-tuple:

$$M = (Q, \Sigma, \Gamma, \delta, q_0, Z_0, F)$$

Where:
- **$Q$**: Finite set of states
- **$\Sigma$**: Finite input alphabet
- **$\Gamma$**: Finite stack alphabet
- **$\delta$**: Transition function, $\delta: Q \times (\Sigma \cup \{\varepsilon\}) \times \Gamma \to \mathcal{P}(Q \times \Gamma^*)$
- **$q_0 \in Q$**: Initial / Start state
- **$Z_0 \in \Gamma$**: Initial bottom-of-stack marker
- **$F \subseteq Q$**: Set of final / accepting states

Transition notation:
$$\delta(q, a, X) = (p, \gamma)$$
Meaning: When the PDA is in state $q$, reads symbol $a$ from the input (or $\varepsilon$ without reading), and finds symbol $X$ on top of the stack, it transitions to state $p$ and replaces $X$ with the string $\gamma$ on the stack.

---

# Topic A: Postfix Arithmetic Expression Evaluation

Evaluates mathematical expressions written in postfix (Reverse Polish) notation using a LIFO stack. Operands are pushed onto the stack, and operators consume the top two operands to push the computed result.

### 1. Formal 7-Tuple Specification
- **$Q$** = $\{q_0, q_{\text{op}}, q_f\}$
- **$\Sigma$** = $\{\text{numbers } c, +, -, *, /, \$\}$
- **$\Gamma$** = $\{\text{numbers/operands}\} \cup \{Z_0\}$
- **$q_0$** = $q_0$ (Evaluation State)
- **$Z_0$** = $Z_0$ (Stack Bottom Marker)
- **$F$** = $\{q_f\}$ (Acceptance State)

### 2. State Transition Table

| Current State ($q$) | Input Symbol ($a$) | Stack Top ($X$) | Next State ($p$) | Replacement on Stack ($\gamma$) | Formal Transition $\delta(q, a, X)$ | Meaning / Operation |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **$q_0$** | Operand $c$ | $X$ | $q_0$ | $c \cdot X$ | $(q_0, cX)$ | **Push operand** onto stack |
| **$q_0$** | Operator $\theta \in \{+, -, *, /\}$ | $Y_1$ | $q_{\text{op}}$ | $\varepsilon$ | $(q_{\text{op}}, \varepsilon)$ | **Read operator**: POP 1st operand ($Y_1$) |
| **$q_{\text{op}}$** | $\varepsilon$ | $Y_2$ | $q_0$ | $(Y_2\ \theta\ Y_1) \cdot X$ | $(q_0, \text{result} \cdot X)$ | **POP 2nd operand** ($Y_2$), compute result, **PUSH result** |
| **$q_0$** | $\$$ (End Marker) | $R$ (with $Z_0$ below) | $q_f$ | $R \cdot Z_0$ | $(q_f, RZ_0)$ | **Accept**: Exactly one result $R$ left on stack |

### 3. Example Trace (`3 4 + 2 * $`)
1. State $q_0$, Input `3`: Stack $= [3, Z_0]$
2. State $q_0$, Input `4`: Stack $= [4, 3, Z_0]$
3. State $q_0$, Input `+`: Pops $4$, enters $q_{\text{op}}$, pops $3$, computes $3+4=7$, pushes $7 \to$ Stack $= [7, Z_0]$, back to $q_0$
4. State $q_0$, Input `2`: Stack $= [2, 7, Z_0]$
5. State $q_0$, Input `*`: Pops $2$, enters $q_{\text{op}}$, pops $7$, computes $7 \times 2 = 14$, pushes $14 \to$ Stack $= [14, Z_0]$
6. State $q_0$, Input `$` : Enters final state $q_f$, Result $= 14$ (ACCEPT).

---

# Topic B: Tower of Hanoi Call Stack Simulation

Models recursive function calls using an explicit PDA stack. Frames represent either sub-problems $R(n, S, D, A)$ or physical disk move commands $M(n, S, D)$.

### 1. Formal 7-Tuple Specification
- **$Q$** = $\{q_0, q_1, q_f\}$
- **$\Sigma$** = $\{(n, S, D, A), \$\}$
- **$\Gamma$** = $\{R(k, s, d, a), M(k, s, d), Z_0\}$
  - $R(k, s, d, a)$: Recursive sub-task "Transfer $k$ disks from peg $s$ to peg $d$ using $a$"
  - $M(k, s, d)$: Direct primitive move instruction "Move disk $k$ from peg $s$ to $d$"
- **$q_0$** = $q_0$
- **$Z_0$** = $Z_0$
- **$F$** = $\{q_f\}$

### 2. State Transition Table

| Current State ($q$) | Input Symbol ($a$) | Stack Top ($X$) | Next State ($p$) | Replacement on Stack ($\gamma$) | Formal Transition $\delta(q, a, X)$ | Meaning / Operation |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **$q_0$** | $(n, S, D, A)$ | $Z_0$ | $q_1$ | $R(n, S, D, A) \cdot Z_0$ | $(q_1, R(n, S, D, A) Z_0)$ | **Read initial problem**, push main recursive task frame |
| **$q_1$** | $\varepsilon$ | $R(1, s, d, a)$ | $q_1$ | $\varepsilon$ | $(q_1, \varepsilon)$ | **Base Case ($k=1$):** POP $R(1)$, emit move "Disk 1: $s \to d$" |
| **$q_1$** | $\varepsilon$ | $R(k, s, d, a)$ <br> *(where $k > 1$)* | $q_1$ | $R(k-1, s, a, d) \\ M(k, s, d) \\ R(k-1, a, d, s)$ | $(q_1, R_1 \cdot M \cdot R_2)$ | **Recursive Expansion:** POP $R(k)$, PUSH 3 sub-tasks in reverse order |
| **$q_1$** | $\varepsilon$ | $M(k, s, d)$ | $q_1$ | $\varepsilon$ | $(q_1, \varepsilon)$ | **Execute Move:** POP $M$, emit move "Disk $k$: $s \to d$" |
| **$q_1$** | $\$$ | $Z_0$ | $q_f$ | $Z_0$ | $(q_f, Z_0)$ | **Accept**: All call frames resolved, stack has only $Z_0$ |

---

# Topic C: HTML / XML Balanced Tag Validation

Validates whether open and close markup tags form properly nested language structures (a classic Context-Free Language $L = \{w \mid \text{tags in } w \text{ are properly nested}\}$).

### 1. Formal 7-Tuple Specification
- **$Q$** = $\{q_0, q_f, q_{\text{err}}\}$
- **$\Sigma$** = $\{\langle t \rangle, \langle /t \rangle, \text{text}, \$\} \quad (\forall t \in \text{Tag Names})$
- **$\Gamma$** = $\{t \mid t \in \text{Tag Names}\} \cup \{Z_0\}$
- **$q_0$** = $q_0$ (Processing State)
- **$Z_0$** = $Z_0$ (Bottom Marker)
- **$F$** = $\{q_f\}$ (Accepting State)

### 2. State Transition Table

| Current State ($q$) | Input Symbol ($a$) | Stack Top ($X$) | Next State ($p$) | Stack Action ($\gamma$) | Formal Transition $\delta(q, a, X)$ | Meaning / Operation |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **$q_0$** | Opening Tag $\langle t \rangle$ | $X$ | $q_0$ | $t \cdot X$ | $(q_0, tX)$ | **Push opening tag** $t$ onto stack |
| **$q_0$** | Text chunk | $X$ | $q_0$ | $X$ | $(q_0, X)$ | Text inside tag: **stack unchanged** |
| **$q_0$** | Closing Tag $\langle /t \rangle$ | $t$ | $q_0$ | $\varepsilon$ | $(q_0, \varepsilon)$ | **Matching Tag: POP** $t$ from stack |
| **$q_0$** | Closing Tag $\langle /t \rangle$ | $t'\ (t' \neq t)$ | $q_{\text{err}}$ | $t'X$ | $(q_{\text{err}}, t'X)$ | **Tag Mismatch Error** (e.g., `<div>...</span>`) |
| **$q_0$** | Closing Tag $\langle /t \rangle$ | $Z_0$ | $q_{\text{err}}$ | $Z_0$ | $(q_{\text{err}}, Z_0)$ | **Extra Closing Tag** when stack has no open tag |
| **$q_0$** | $\$$ (End of Input) | $Z_0$ | $q_f$ | $Z_0$ | $(q_f, Z_0)$ | **Accept**: All tags matched and closed |
| **$q_0$** | $\$$ (End of Input) | $t \neq Z_0$ | $q_{\text{err}}$ | $tX$ | $(q_{\text{err}}, tX)$ | **Unclosed Tag Error**: Input ended with tags still open |

---

# Topic D: Natural Language Processing (Shift-Reduce Parser)

Parses natural English sentences into hierarchical phrase structure trees (Parse / Syntax Trees) via bottom-up Shift-Reduce parsing simulated on a PDA stack.

### 1. Formal 7-Tuple Specification
- **$Q$** = $\{q_0, q_1, q_f, q_{\text{err}}\}$
- **$\Sigma$** = $\{\text{words in lexicon: } \text{the}, \text{a}, \text{dog}, \text{cat}, \text{chased}, \text{saw}, \dots\} \cup \{\$\}$
- **$\Gamma$** = $\Sigma \cup \{\text{Det}, \text{N}, \text{V}, \text{Adj}, \text{Adv}, \text{NP}, \text{VP}, \text{S}, Z_0\}$
- **$q_0$** = $q_0$ (Start)
- **$Z_0$** = $Z_0$ (Bottom Marker)
- **$F$** = $\{q_f\}$ (Accept)

### 2. Underlying Context-Free Grammar (CFG) Rules
- $S \to NP\ VP$
- $VP \to V\ NP \mid V \mid Adv\ VP$
- $NP \to Det\ Adj\ N \mid Det\ N$
- Lexical rules: $Det \to \text{the} \mid \text{a}$, $N \to \text{dog} \mid \text{cat}$, $V \to \text{chased} \mid \text{saw}$, etc.

### 3. State Transition Table

| Current State ($q$) | Input Symbol ($a$) | Stack Top ($X$) | Next State ($p$) | Stack Action ($\gamma$) | Formal Transition $\delta(q, a, X)$ | Meaning / Operation |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **$q_0$** | $\varepsilon$ | $Z_0$ | $q_1$ | $Z_0$ | $(q_1, Z_0)$ | Transition into Shift-Reduce parsing state $q_1$ |
| **$q_1$** | Word $w \in \Sigma$ | $X$ | $q_1$ | $w \cdot X$ | $(q_1, wX)$ | **SHIFT**: Read next input word, push to stack |
| **$q_1$** | $\varepsilon$ | Word $w$ | $q_1$ | $\text{POS}(w) \cdot X$ | $(q_1, \text{POS} \cdot X)$ | **LEXICAL REDUCE**: Replace word with POS category tag |
| **$q_1$** | $\varepsilon$ | $\text{Det} \cdot \text{N}$ | $q_1$ | $\text{NP}$ | $(q_1, \text{NP})$ | **STRUCTURAL REDUCE**: $NP \to Det\ N$ |
| **$q_1$** | $\varepsilon$ | $\text{Det} \cdot \text{Adj} \cdot \text{N}$ | $q_1$ | $\text{NP}$ | $(q_1, \text{NP})$ | **STRUCTURAL REDUCE**: $NP \to Det\ Adj\ N$ |
| **$q_1$** | $\varepsilon$ | $\text{V} \cdot \text{NP}$ | $q_1$ | $\text{VP}$ | $(q_1, \text{VP})$ | **STRUCTURAL REDUCE**: $VP \to V\ NP$ (Transitive verb phrase) |
| **$q_1$** | $\varepsilon$ | $\text{V}$ *(lookahead)* | $q_1$ | $\text{VP}$ | $(q_1, \text{VP})$ | **STRUCTURAL REDUCE**: $VP \to V$ (Intransitive verb phrase) |
| **$q_1$** | $\varepsilon$ | $\text{Adv} \cdot \text{VP}$ | $q_1$ | $\text{VP}$ | $(q_1, \text{VP})$ | **STRUCTURAL REDUCE**: $VP \to Adv\ VP$ |
| **$q_1$** | $\varepsilon$ | $\text{NP} \cdot \text{VP}$ | $q_1$ | $\text{S}$ | $(q_1, \text{S})$ | **STRUCTURAL REDUCE**: $S \to NP\ VP$ (Sentence root) |
| **$q_1$** | $\$$ | $\text{S} \cdot Z_0$ | $q_f$ | $Z_0$ | $(q_f, Z_0)$ | **ACCEPT**: Sentence fully reduced to Start symbol $S$ |
| **$q_1$** | $\$$ | Any $\neq \text{S} \cdot Z_0$ | $q_{\text{err}}$ | Stack | $(q_{\text{err}}, \text{Stack})$ | **REJECT / ERROR**: Cannot reduce remaining stack to $S$ |
