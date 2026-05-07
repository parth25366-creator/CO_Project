# CO Project 2026 — RV32I Assembler & Simulator

A complete implementation of a **two-pass RV32I assembler** and a **RISC-V 32-bit simulator**, built for the Computer Organization course (CSE 112) at IIIT Delhi.

---

## 📁 Project Structure

```
CO_Project/
├── SimpleAssembler/
│   ├── Assembler.py        ← Two-pass RV32I assembler
│   ├── test.asm            ← Sample assembly program
│   └── output.txt          ← Sample assembled output
│
├── SimpleSimulator/
│   └── Simulator.py        ← RV32I simulator with memory & trace output
│
├── automatedTesting/
│   ├── src/                ← Grader scripts (do NOT modify)
│   └── tests/
│       ├── assembly/
│       │   ├── simpleBin/      ← Easy assembly input test cases
│       │   ├── hardBin/        ← Hard assembly input test cases
│       │   ├── errorGen/       ← Error-triggering assembly programs
│       │   ├── bin_s/          ← Golden outputs for simpleBin
│       │   ├── bin_h/          ← Golden outputs for hardBin
│       │   ├── user_bin_s/     ← Your assembler's output (simple)
│       │   └── user_bin_h/     ← Your assembler's output (hard)
│       ├── bin/
│       │   ├── simple/         ← Easy machine-code simulator inputs
│       │   └── hard/           ← Hard machine-code simulator inputs
│       ├── traces/
│       │   ├── simple/         ← Golden simulator traces (simple)
│       │   └── hard/           ← Golden simulator traces (hard)
│       └── user_traces/
│           ├── simple/         ← Your simulator's traces (simple)
│           └── hard/           ← Your simulator's traces (hard)
│
└── README.md
```

---

## ⚙️ How It Works

### Assembler (`SimpleAssembler/Assembler.py`)

A **two-pass assembler** that translates RV32I assembly into 32-bit binary machine code.

**Pass 1 — Symbol Table:**  
Scans through the file, tracking the PC (starts at `0x00000000`, increments by 4 per instruction). Every label found is recorded with its corresponding PC address.

**Pass 2 — Encoding:**  
Revisits each instruction and encodes it into a 32-bit binary string using the correct RISC-V format (R / I / S / B / U / J). Branch and jump offsets are computed as `target_address - current_PC`.

**Supported Instructions:**

| Format | Instructions |
|--------|-------------|
| R-type | `add`, `sub`, `sll`, `slt`, `sltu`, `xor`, `srl`, `or`, `and` |
| I-type | `addi`, `sltiu`, `lw`, `jalr` |
| S-type | `sw` |
| B-type | `beq`, `bne`, `blt`, `bge`, `bltu`, `bgeu` |
| U-type | `lui`, `auipc` |
| J-type | `jal` |
| Virtual Halt | `beq zero, zero, 0` — **required in every program** |

**Usage:**
```bash
python3 Assembler.py <input.asm> <output.bin> [readable.txt]
```

Example:
```bash
python3 Assembler.py test.asm output.txt readable.txt
```

---

### Simulator (`SimpleSimulator/Simulator.py`)

Executes binary machine code produced by the assembler. Decodes each 32-bit instruction, updates registers and memory, and writes a **trace log** of the machine state after each instruction.

**Memory Map:**

| Region       | Address Range               | Notes                        |
|--------------|-----------------------------|------------------------------|
| Program      | `0x00000000` – `0x000000FF` | Max 64 instructions (256 B)  |
| Stack        | `0x00000100` – `0x0000017F` | `sp` initialised to `0x17C`, grows down |
| Data         | `0x00010000` – `0x0001007F` | 128 bytes for heap/data use  |

**Trace Format (one line per instruction executed):**
```
<next_PC> <x0> <x1> <x2> ... <x31>
```
All values are 32-bit binary strings prefixed with `0b`.

**Memory Dump (on halt):**
Appends 32 lines of data-memory content:
```
0x00010000:0b00000000000000000000000000000000
0x00010004:0b...
...
```

**Halt Condition:**  
The simulator stops when it encounters the virtual halt instruction `beq zero, zero, 0` (`00000000000000000000000001100011`). The final machine state (PC + all registers + data memory) is written to the output trace.

**Error Handling:**
- Out-of-bounds PC → terminates immediately (no trace line)
- Unaligned memory access → terminates immediately
- Invalid memory region access → terminates immediately
- Unknown opcode → terminates immediately

**Usage:**
```bash
python3 Simulator.py <input.bin> <output_trace.txt> [readable.txt]
```

Example:
```bash
python3 Simulator.py output.txt trace.txt readable.txt
```

---

## 🧪 Running the Automated Grader

Always run grader commands from **inside the `automatedTesting/` directory**.

```bash
cd automatedTesting
```

| Task | Linux | Windows |
|------|-------|---------|
| Run assembler tests only | `python3 src/main.py --no-sim --linux` | `python3 src\main.py --no-sim --windows` |
| Run simulator tests only | `python3 src/main.py --no-asm --linux` | `python3 src\main.py --no-asm --windows` |
| Run both | `python3 src/main.py --linux` | `python3 src\main.py --windows` |
| Clear old outputs first | `python3 src/main.py --linux --clear-residue` | `python3 src\main.py --windows --clear-residue` |

The grader compares your output files (in `user_bin_*` / `user_traces/`) against the golden reference files (in `bin_s/`, `bin_h/`, `traces/`) and reports marks.

> ⚠️ **File naming is strict.** If the input is `simple_1.txt`, the golden output must also be named `simple_1.txt`.

---

## 🔴 Common Errors & Fixes

| Error | Likely Cause |
|-------|-------------|
| `Unknown instruction` | Typo in opcode or using an unsupported instruction |
| `Undefined label` | Label referenced before or without definition |
| `Missing virtual halt` | Every program must end with `beq zero, zero, 0` |
| `Invalid memory access` | `lw`/`sw` to an address outside the allowed regions |
| `Unaligned access` | Address not a multiple of 4 for `lw`/`sw` |
| `PC out of bounds` | Jump/branch target outside the program region |

---

## 📌 Notes

- Both scripts follow the **3-argument interface**: `<input> <output> [readable]`. The grader always passes all 3, so make sure your scripts accept them.
- `x0` is hardwired to `0` — any write to it is silently discarded.
- The assembler does **not** write any output file if an error is detected.
- The simulator does **not** write a trace line for the cycle that caused a fatal error.

---

*Built for CSE 112 — Computer Organization, IIIT Delhi, Semester II 2025–26.*
