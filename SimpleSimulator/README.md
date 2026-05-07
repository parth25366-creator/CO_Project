# SimpleSimulator — RV32I Simulator

A Python-based simulator for the RISC-V 32-bit ISA (RV32I subset), built for the CO Project 2026 at IIIT Delhi.  
Takes binary machine code (produced by the assembler) as input, executes it instruction-by-instruction, and outputs a full trace log of the machine state.

---

## 🚀 Usage

```bash
python3 Simulator.py <input.bin> <output_trace.txt> [readable.txt]
```

- `input.bin` — machine code file (one 32-bit binary string per line)
- `output_trace.txt` — trace output written here
- `readable.txt` — optional human-readable dump (pass anything, grader sends 3 args)

**Example:**
```bash
python3 Simulator.py ../SimpleAssembler/output.txt trace.txt readable.txt
```

---

## 🧠 How It Works

### 1. Loading
Each line of the input file is a 32-bit binary string (e.g. `00000000001000001000000010110011`).  
They are loaded into the program memory region starting at address `0x00000000`, spaced 4 bytes apart.

### 2. Execution Loop
The simulator fetches the instruction at the current `PC`, decodes it by opcode, executes it, and advances the PC. After every instruction (except on error or halt), it records a **trace line**.

### 3. Halt
Execution stops when the **virtual halt** instruction is encountered:
```
beq zero, zero, 0  →  00000000000000000000000001100011
```
On halt: the final machine state (PC + registers) is traced, then the **data memory dump** is appended.

### 4. Errors
On any fatal error, the simulator prints a message and exits **immediately** — no trace line or memory dump is written for that cycle.

---

## 🗺️ Memory Map

| Region   | Start        | End          | Size    | Notes                              |
|----------|--------------|--------------|---------|------------------------------------|
| Program  | `0x00000000` | `0x000000FF` | 256 B   | Max 64 instructions, read-only     |
| Stack    | `0x00000100` | `0x0000017F` | 128 B   | `sp` = `0x0000017C`, grows down    |
| Data     | `0x00010000` | `0x0001007F` | 128 B   | General-purpose read/write         |

> Reads are allowed from Program + Stack + Data.  
> Writes are only allowed to Stack + Data.

---

## 📄 Output Format

### Trace Line (one per instruction executed)
```
<PC> <x0> <x1> <x2> ... <x31>
```
- All values are **32-bit binary strings** prefixed with `0b`
- PC shown is the **next** PC (after the instruction executes), except on halt where it stays the same
- 33 space-separated values per line (1 PC + 32 registers)

**Example line:**
```
0b00000000000000000000000000001000 0b00000000000000000000000000000000 0b00000000000000000000000000000001 ...
```

### Memory Dump (appended on halt only)
32 lines covering the entire data memory region:
```
0x00010000:0b00000000000000000000000000000000
0x00010004:0b00000000000000000000000000000000
...
0x0001007C:0b00000000000000000000000000000000
```

---

## 📦 Supported Instructions

| Format   | Instructions                                      |
|----------|---------------------------------------------------|
| R-type   | `add`, `sub`, `sll`, `slt`, `sltu`, `xor`, `srl`, `or`, `and` |
| I-type   | `addi`, `sltiu`, `lw`, `jalr`                    |
| S-type   | `sw`                                              |
| B-type   | `beq`, `bne`, `blt`, `bge`, `bltu`, `bgeu`       |
| U-type   | `lui`, `auipc`                                    |
| J-type   | `jal`                                             |
| Halt     | `beq zero, zero, 0` (virtual halt)               |

---

## ⚠️ Error Conditions

| Error | Trigger |
|-------|---------|
| `PC out of bounds` | PC points outside the loaded program |
| `Unknown opcode` | Instruction bits don't match any known opcode |
| `Unaligned memory access` | `lw`/`sw` address not divisible by 4 |
| `Invalid memory region` | Access to an address outside all valid regions |

All errors terminate execution immediately with no output for that cycle.

---

## 📝 Key Implementation Details

- **`x0` is hardwired to 0** — any write to register 0 is silently discarded
- **Sign extension** is applied correctly for I, S, B, J-type immediates
- **`sp` (x2)** is initialised to `0x0000017C` at startup
- Memory is **sparse** (Python dict), so unwritten addresses read as `0`
- `jalr` clears the LSB of the target address (`& 0xFFFFFFFE`) per the spec
- All register values are masked to **32 bits unsigned** on every write

---

*Part of CSE 112 — Computer Organization, IIIT Delhi, Semester II 2025–26.*
