import sys

# ----------------------------------------
# REGISTER MAP (x registers + ABI names)
# ----------------------------------------

REGISTER_MAP = {
    **{f"x{i}": format(i, "05b") for i in range(32)},

    "zero": format(0, "05b"),
    "ra": format(1, "05b"),
    "sp": format(2, "05b"),
    "gp": format(3, "05b"),
    "tp": format(4, "05b"),

    "t0": format(5, "05b"),
    "t1": format(6, "05b"),
    "t2": format(7, "05b"),

    "s0": format(8, "05b"),
    "fp": format(8, "05b"),
    "s1": format(9, "05b"),

    "a0": format(10, "05b"),
    "a1": format(11, "05b"),
    "a2": format(12, "05b"),
    "a3": format(13, "05b"),
    "a4": format(14, "05b"),
    "a5": format(15, "05b"),
    "a6": format(16, "05b"),
    "a7": format(17, "05b"),

    "s2": format(18, "05b"),
    "s3": format(19, "05b"),
    "s4": format(20, "05b"),
    "s5": format(21, "05b"),
    "s6": format(22, "05b"),
    "s7": format(23, "05b"),
    "s8": format(24, "05b"),
    "s9": format(25, "05b"),
    "s10": format(26, "05b"),
    "s11": format(27, "05b"),

    "t3": format(28, "05b"),
    "t4": format(29, "05b"),
    "t5": format(30, "05b"),
    "t6": format(31, "05b"),
}

# ----------------------------------------
# OPCODE TABLE
# ----------------------------------------

OPCODE_TABLE = {
    # R-type
    "add":  {"type": "R", "opcode": "0110011", "funct3": "000", "funct7": "0000000"},
    "sub":  {"type": "R", "opcode": "0110011", "funct3": "000", "funct7": "0100000"},
    "slt":  {"type": "R", "opcode": "0110011", "funct3": "010", "funct7": "0000000"},
    "srl":  {"type": "R", "opcode": "0110011", "funct3": "101", "funct7": "0000000"},

    # I-type
    "addi": {"type": "I", "opcode": "0010011", "funct3": "000"},
    "lw":   {"type": "I", "opcode": "0000011", "funct3": "010"},
    "jalr": {"type": "I", "opcode": "1100111", "funct3": "000"},

    # S-type
    "sw":   {"type": "S", "opcode": "0100011", "funct3": "010"},

    # B-type
    "beq":  {"type": "B", "opcode": "1100011", "funct3": "000"},
    "bne":  {"type": "B", "opcode": "1100011", "funct3": "001"},

    # U-type
    "lui":   {"type": "U", "opcode": "0110111"},
    "auipc": {"type": "U", "opcode": "0010111"},

    # J-type
    "jal":  {"type": "J", "opcode": "1101111"},
}

# ----------------------------------------
# UTILITIES
# ----------------------------------------

def to_binary(value, bits):
    value = int(value)
    if value < 0:
        value = (1 << bits) + value
    return format(value, f"0{bits}b")

def clean_line(line):
    line = line.split("#")[0]
    return line.strip()

# ----------------------------------------
# FIRST PASS
# ----------------------------------------

def first_pass(lines):
    symbol_table = {}
    pc = 0

    for line in lines:
        if ":" in line:
            label, rest = line.split(":")
            symbol_table[label.strip()] = pc
            if rest.strip() != "":
                pc += 4
        else:
            pc += 4

    return symbol_table

# ----------------------------------------
# ENCODERS
# ----------------------------------------

def encode_R(parts):
    info = OPCODE_TABLE[parts[0]]
    rd = REGISTER_MAP[parts[1]]
    rs1 = REGISTER_MAP[parts[2]]
    rs2 = REGISTER_MAP[parts[3]]
    return info["funct7"] + rs2 + rs1 + info["funct3"] + rd + info["opcode"]

def encode_I(parts):
    instr = parts[0]
    info = OPCODE_TABLE[instr]
    rd = REGISTER_MAP[parts[1]]

    if instr == "lw":
        imm, rs1 = parts[2].split("(")
        rs1 = rs1.replace(")", "")
        rs1 = REGISTER_MAP[rs1]
    else:
        rs1 = REGISTER_MAP[parts[2]]
        imm = parts[3]

    imm_bin = to_binary(imm, 12)
    return imm_bin + rs1 + info["funct3"] + rd + info["opcode"]

def encode_S(parts):
    info = OPCODE_TABLE[parts[0]]
    rs2 = REGISTER_MAP[parts[1]]
    imm, rs1 = parts[2].split("(")
    rs1 = rs1.replace(")", "")
    rs1 = REGISTER_MAP[rs1]

    imm_bin = to_binary(imm, 12)
    return imm_bin[:7] + rs2 + rs1 + info["funct3"] + imm_bin[7:] + info["opcode"]

def encode_B(parts, pc, symbol_table):
    info = OPCODE_TABLE[parts[0]]
    rs1 = REGISTER_MAP[parts[1]]
    rs2 = REGISTER_MAP[parts[2]]

    if parts[3] in symbol_table:
        offset = symbol_table[parts[3]] - pc
    else:
        offset = int(parts[3])

    imm = to_binary(offset, 13)

    # Correct B-type bit placement
    return (
        imm[0] +          # imm[12]
        imm[2:8] +        # imm[10:5]
        rs2 +
        rs1 +
        info["funct3"] +
        imm[8:12] +       # imm[4:1]
        imm[1] +          # imm[11]
        info["opcode"]
    )

def encode_U(parts):
    info = OPCODE_TABLE[parts[0]]
    rd = REGISTER_MAP[parts[1]]
    imm_bin = to_binary(parts[2], 20)
    return imm_bin + rd + info["opcode"]

def encode_J(parts, pc, symbol_table):
    info = OPCODE_TABLE[parts[0]]
    rd = REGISTER_MAP[parts[1]]

    if parts[2] in symbol_table:
        offset = symbol_table[parts[2]] - pc
    else:
        offset = int(parts[2])

    imm = to_binary(offset, 21)

    # Correct J-type placement
    return (
        imm[0] +          # imm[20]
        imm[10:20] +      # imm[10:1]
        imm[9] +          # imm[11]
        imm[1:9] +        # imm[19:12]
        rd +
        info["opcode"]
    )

# ----------------------------------------
# SECOND PASS
# ----------------------------------------

def second_pass(lines, symbol_table):
    pc = 0
    output = []

    for line in lines:
        if ":" in line:
            if line.strip().endswith(":"):
                continue
            else:
                line = line.split(":")[1].strip()

        line = line.replace(",", " ")
        parts = line.split()

        instr = parts[0]
        instr_type = OPCODE_TABLE[instr]["type"]

        if instr_type == "R":
            binary = encode_R(parts)
        elif instr_type == "I":
            binary = encode_I(parts)
        elif instr_type == "S":
            binary = encode_S(parts)
        elif instr_type == "B":
            binary = encode_B(parts, pc, symbol_table)
        elif instr_type == "U":
            binary = encode_U(parts)
        elif instr_type == "J":
            binary = encode_J(parts, pc, symbol_table)

        output.append(binary)
        pc += 4

    return output

# ----------------------------------------
# MAIN
# ----------------------------------------

def main():
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, "r") as f:
        raw_lines = f.readlines()

    lines = []
    for line in raw_lines:
        cleaned = clean_line(line)
        if cleaned:
            lines.append(cleaned)

    symbol_table = first_pass(lines)
    binary_output = second_pass(lines, symbol_table)

    with open(output_file, "w") as f:
        f.write("\n".join(binary_output))

if __name__ == "__main__":
    main()
