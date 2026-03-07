# RV32I Assembler - CO Project 2026

two-pass assembler for a subset of the RISC-V 32-bit ISA, written in Python.

---

## how to run

```
python3 Assembler.py input.asm output.bin readable.txt
```

the grader passes 3 arguments so make sure you run it that way too.
if you just want to test manually:

```
python3 Assembler.py test.asm out.txt out_r.txt
```

to run via the grader (from inside `automatedTesting/`):

```
python3 src/main.py --no-sim --linux
```

---

## what it does

reads an assembly file and converts every instruction into a 32-bit binary string.
one line of binary output per instruction.

if there's any error, it prints what went wrong and exits without writing anything.

---

## design - two pass approach

we need two passes because of forward references. if a branch says `bne t0, a0, loop`
but `loop:` appears later in the file, we don't know its address yet during the first read.

**pass 1** - scan everything, build a symbol table:
```
{ "loop": 16, "done": 48, ... }
```
PC starts at 0, goes up by 4 for each instruction. label-only lines don't count.

**pass 2** - actually encode every instruction.
for branches and jumps: `offset = label_address - current_pc`
then pack all the fields into a 32-bit string based on the instruction type.

---

## instruction types

RISC-V has 6 formats. the opcode (bits 6:0) tells you which format it is.

**R-type** - reg-reg operations (add, sub, xor, etc.)
```
[ funct7 | rs2 | rs1 | funct3 | rd | opcode ]
   7 bits  5b   5b    3 bits   5b   7 bits
```

**I-type** - immediate ops, loads, jalr
```
[ imm[11:0] | rs1 | funct3 | rd | opcode ]
   12 bits    5b    3 bits   5b   7 bits
```

**S-type** - stores (sw)
```
[ imm[11:5] | rs2 | rs1 | funct3 | imm[4:0] | opcode ]
```
note: immediate is split into two pieces to keep rs1/rs2 at fixed positions.

**B-type** - branches (beq, bne, blt, etc.)
```
[ imm[12,10:5] | rs2 | rs1 | funct3 | imm[4:1,11] | opcode ]
```
offset is PC-relative. bit 0 is always 0 (instructions are aligned) so it's implicit.
the immediate bits are scrambled - annoying but keeps decode hardware simple.

**U-type** - lui, auipc
```
[ imm[31:12] | rd | opcode ]
   20 bits     5b   7 bits
```

**J-type** - jal
```
[ imm[20,10:1,11,19:12] | rd | opcode ]
```
same scrambling idea as B-type. offset is PC-relative.

---

## supported instructions

R-type : add, sub, sll, slt, sltu, xor, srl, or, and
I-type : addi, sltiu, lw, jalr
S-type : sw
B-type : beq, bne, blt, bge, bltu, bgeu
U-type : lui, auipc
J-type : jal

virtual halt : beq zero,zero,0  (must be in every program, simulator stops here)

---

## errors it catches

- unknown instruction name
- invalid register (like t56 or x99)
- undefined label
- missing virtual halt
- bad syntax in general

---

## memory layout (for reference)

- program memory : 0x00000000 to 0x000000FF (256 bytes, max 64 instructions)
- stack          : 0x00000100 to 0x0000017F, sp starts at 0x0000017C, grows down
- data memory    : 0x00010000 to 0x0001007F (128 bytes)

---

## folder structure

```
CO_Project/
  SimpleAssembler/
    Assembler.py
    readme.txt
    test.asm
    output.txt
  SimpleSimulator/
    ...
  automatedTesting/
    src/          <- grader, don't touch
    tests/
      assembly/simpleBin/    <- input test cases
      assembly/bin_s/        <- expected output
      assembly/user_bin_s/   <- your output goes here
      assembly/errorGen/     <- error test cases
```
