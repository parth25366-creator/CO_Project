import sys

# maps every register name (both x0-x31 and ABI names) to its 5-bit binary string
REGISTER_MAP = {
    **{f"x{i}": format(i, "05b") for i in range(32)},
    "zero": format(0,  "05b"),
    "ra":   format(1,  "05b"),
    "sp":   format(2,  "05b"),
    "gp":   format(3,  "05b"),
    "tp":   format(4,  "05b"),
    "t0":   format(5,  "05b"),
    "t1":   format(6,  "05b"),
    "t2":   format(7,  "05b"),
    "s0":   format(8,  "05b"),
    "fp":   format(8,  "05b"),
    "s1":   format(9,  "05b"),
    "a0":   format(10, "05b"),
    "a1":   format(11, "05b"),
    "a2":   format(12, "05b"),
    "a3":   format(13, "05b"),
    "a4":   format(14, "05b"),
    "a5":   format(15, "05b"),
    "a6":   format(16, "05b"),
    "a7":   format(17, "05b"),
    "s2":   format(18, "05b"),
    "s3":   format(19, "05b"),
    "s4":   format(20, "05b"),
    "s5":   format(21, "05b"),
    "s6":   format(22, "05b"),
    "s7":   format(23, "05b"),
    "s8":   format(24, "05b"),
    "s9":   format(25, "05b"),
    "s10":  format(26, "05b"),
    "s11":  format(27, "05b"),
    "t3":   format(28, "05b"),
    "t4":   format(29, "05b"),
    "t5":   format(30, "05b"),
    "t6":   format(31, "05b"),
}

# for each mnemonic, stores the type and all the fixed encoding fields
OPCODE_TABLE = {
    # R-type (opcode 0110011) - all reg-reg arithmetic
    "add":  {"type": "R", "opcode": "0110011", "funct3": "000", "funct7": "0000000"},
    "sub":  {"type": "R", "opcode": "0110011", "funct3": "000", "funct7": "0100000"},
    "sll":  {"type": "R", "opcode": "0110011", "funct3": "001", "funct7": "0000000"},
    "slt":  {"type": "R", "opcode": "0110011", "funct3": "010", "funct7": "0000000"},
    "sltu": {"type": "R", "opcode": "0110011", "funct3": "011", "funct7": "0000000"},
    "xor":  {"type": "R", "opcode": "0110011", "funct3": "100", "funct7": "0000000"},
    "srl":  {"type": "R", "opcode": "0110011", "funct3": "101", "funct7": "0000000"},
    "or":   {"type": "R", "opcode": "0110011", "funct3": "110", "funct7": "0000000"},
    "and":  {"type": "R", "opcode": "0110011", "funct3": "111", "funct7": "0000000"},

    # I-type - immediate arithmetic + loads + jalr
    "addi":  {"type": "I", "opcode": "0010011", "funct3": "000"},
    "sltiu": {"type": "I", "opcode": "0010011", "funct3": "011"},
    "lw":    {"type": "I", "opcode": "0000011", "funct3": "010"},
    "jalr":  {"type": "I", "opcode": "1100111", "funct3": "000"},

    # S-type - stores
    "sw":    {"type": "S", "opcode": "0100011", "funct3": "010"},

    # B-type - branches (all share opcode 1100011, funct3 tells which branch)
    "beq":   {"type": "B", "opcode": "1100011", "funct3": "000"},
    "bne":   {"type": "B", "opcode": "1100011", "funct3": "001"},
    "blt":   {"type": "B", "opcode": "1100011", "funct3": "100"},
    "bge":   {"type": "B", "opcode": "1100011", "funct3": "101"},
    "bltu":  {"type": "B", "opcode": "1100011", "funct3": "110"},
    "bgeu":  {"type": "B", "opcode": "1100011", "funct3": "111"},

    # U-type - load upper immediate
    "lui":   {"type": "U", "opcode": "0110111"},
    "auipc": {"type": "U", "opcode": "0010111"},

    # J-type - jump and link
    "jal":   {"type": "J", "opcode": "1101111"},
}


def to_binary(value, num_bits):
    # converts an int to two's complement binary of given width
    value = int(value)
    if value < 0:
        value = (1 << num_bits) + value
    return format(value, f"0{num_bits}b")


def clean_line(line):
    # strip comments (everything after #) and whitespace
    return line.split("#")[0].strip()


def first_pass(lines):
    # go through every line and record where each label is (its byte address)
    # this is needed so we can resolve forward references in pass 2
    symbol_table = {}
    pc = 0
    for line in lines:
        if ":" in line:
            label, rest = line.split(":", 1)
            symbol_table[label.strip()] = pc
            if rest.strip() != "":
                pc += 4   # label is on same line as an instruction
        else:
            pc += 4
    return symbol_table


def encode_R(tokens):
    # format: funct7 | rs2 | rs1 | funct3 | rd | opcode
    info = OPCODE_TABLE[tokens[0]]
    rd   = REGISTER_MAP[tokens[1]]
    rs1  = REGISTER_MAP[tokens[2]]
    rs2  = REGISTER_MAP[tokens[3]]
    return info["funct7"] + rs2 + rs1 + info["funct3"] + rd + info["opcode"]


def encode_I(tokens):
    # format: imm[11:0] | rs1 | funct3 | rd | opcode
    # lw and jalr use  imm(rs1)  syntax, others use  rs1, imm
    info = OPCODE_TABLE[tokens[0]]
    rd   = REGISTER_MAP[tokens[1]]

    if tokens[0] in ("lw", "jalr") and "(" in tokens[2]:
        imm_str, rs1_str = tokens[2].split("(")
        rs1 = REGISTER_MAP[rs1_str.replace(")", "")]
        imm = imm_str
    else:
        rs1 = REGISTER_MAP[tokens[2]]
        imm = tokens[3]

    imm_bin = to_binary(imm, 12)
    return imm_bin + rs1 + info["funct3"] + rd + info["opcode"]


def encode_S(tokens):
    # format: imm[11:5] | rs2 | rs1 | funct3 | imm[4:0] | opcode
    # the 12-bit immediate is split across two places in the instruction
    info    = OPCODE_TABLE[tokens[0]]
    rs2     = REGISTER_MAP[tokens[1]]
    imm_str, rs1_str = tokens[2].split("(")
    rs1     = REGISTER_MAP[rs1_str.replace(")", "")]
    imm_bin = to_binary(imm_str, 12)
    return imm_bin[:7] + rs2 + rs1 + info["funct3"] + imm_bin[7:] + info["opcode"]


def encode_B(tokens, current_pc, symbol_table):
    # format: imm[12,10:5] | rs2 | rs1 | funct3 | imm[4:1,11] | opcode
    # offset = target address - current pc  (PC-relative)
    # bit 0 of offset is always 0 so it's not stored -> encode 13 bits, store 12
    info   = OPCODE_TABLE[tokens[0]]
    rs1    = REGISTER_MAP[tokens[1]]
    rs2    = REGISTER_MAP[tokens[2]]
    target = tokens[3]
    offset = symbol_table[target] - current_pc if target in symbol_table else int(target)

    b = to_binary(offset, 13)
    # scramble: [12] [10:5] rs2 rs1 funct3 [4:1] [11] opcode
    return b[0] + b[2:8] + rs2 + rs1 + info["funct3"] + b[8:12] + b[1] + info["opcode"]


def encode_U(tokens):
    # format: imm[31:12] | rd | opcode  (straight 20-bit immediate)
    info    = OPCODE_TABLE[tokens[0]]
    rd      = REGISTER_MAP[tokens[1]]
    imm_bin = to_binary(tokens[2], 20)
    return imm_bin + rd + info["opcode"]


def encode_J(tokens, current_pc, symbol_table):
    # format: imm[20,10:1,11,19:12] | rd | opcode
    # same idea as B-type - offset is PC-relative, bit 0 implicit
    info   = OPCODE_TABLE[tokens[0]]
    rd     = REGISTER_MAP[tokens[1]]
    target = tokens[2]
    offset = symbol_table[target] - current_pc if target in symbol_table else int(target)

    b = to_binary(offset, 21)
    # scramble: [20] [10:1] [11] [19:12] rd opcode
    return b[0] + b[10:20] + b[9] + b[1:9] + rd + info["opcode"]


def second_pass(lines, symbol_table):
    # encode every instruction into a 32-bit binary string
    pc = 0
    output_lines = []

    for line in lines:
        try:
            # if there's a label prefix, strip it
            if ":" in line:
                if line.strip().endswith(":"):
                    continue  # label-only line, nothing to encode
                line = line.split(":", 1)[1].strip()

            tokens   = line.replace(",", " ").split()
            mnemonic = tokens[0]

            if mnemonic not in OPCODE_TABLE:
                print(f"Error: unknown instruction '{mnemonic}'")
                sys.exit(1)

            t = OPCODE_TABLE[mnemonic]["type"]

            if t == "R":
                binary = encode_R(tokens)
            elif t == "I":
                binary = encode_I(tokens)
            elif t == "S":
                binary = encode_S(tokens)
            elif t == "B":
                binary = encode_B(tokens, pc, symbol_table)
            elif t == "U":
                binary = encode_U(tokens)
            elif t == "J":
                binary = encode_J(tokens, pc, symbol_table)

            output_lines.append(binary)
            pc += 4

        except (KeyError, ValueError) as e:
            print(f"Error on line '{line}': {e}")
            sys.exit(1)

    return output_lines


def main():
    if len(sys.argv) < 3:
        print("usage: python3 Assembler.py <input.asm> <output.bin> [readable.txt]")
        sys.exit(1)

    input_file  = sys.argv[1]
    output_file = sys.argv[2]
    # sys.argv[3] is the readable file path that the grader passes - we accept it but don't use it

    try:
        with open(input_file, "r") as f:
            raw_lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: can't find input file '{input_file}'")
        sys.exit(1)

    # clean up lines
    cleaned = []
    for line in raw_lines:
        c = clean_line(line)
        if c:
            cleaned.append(c)

    # every valid program needs a virtual halt: beq zero,zero,0
    has_halt = any(
        "beq" in line and "zero" in line and
        line.replace(",", " ").split()[-1] in ("0", "0x0")
        for line in cleaned
    )
    if not has_halt:
        print("Error: no virtual halt found (need beq zero,zero,0)")
        sys.exit(1)

    symbol_table = first_pass(cleaned)
    binary_lines = second_pass(cleaned, symbol_table)

    with open(output_file, "w") as f:
        f.write("\n".join(binary_lines))


if __name__ == "__main__":
    main()
