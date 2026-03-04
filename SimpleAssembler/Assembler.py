import sys

# ----------------------------------------
# REGISTER MAP
# ----------------------------------------

REGISTER_MAP = {f"x{i}": format(i, "05b") for i in range(32)}

# ----------------------------------------
# OPCODE TABLE
# ----------------------------------------

OPCODE_TABLE = {
    "add":  {"type": "R", "opcode": "0110011", "funct3": "000", "funct7": "0000000"},
    "sub":  {"type": "R", "opcode": "0110011", "funct3": "000", "funct7": "0100000"},
    
    "addi": {"type": "I", "opcode": "0010011", "funct3": "000"},
    "lw":   {"type": "I", "opcode": "0000011", "funct3": "010"},
    "jalr": {"type": "I", "opcode": "1100111", "funct3": "000"},
    
    "sw":   {"type": "S", "opcode": "0100011", "funct3": "010"},
    
    "beq":  {"type": "B", "opcode": "1100011", "funct3": "000"},
    
    "lui":  {"type": "U", "opcode": "0110111"},
    "auipc":{"type": "U", "opcode": "0010111"},
    
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
# FIRST PASS (LABEL COLLECTION)
# ----------------------------------------

def first_pass(lines):
    symbol_table = {}
    pc = 0
    
    for line in lines:
        if ":" in line:
            label = line.replace(":", "").strip()
            symbol_table[label] = pc
        else:
            pc += 4

    return symbol_table


# ----------------------------------------
# ENCODERS
# ----------------------------------------

def encode_R(parts):
    instr = parts[0]
    rd = REGISTER_MAP[parts[1]]
    rs1 = REGISTER_MAP[parts[2]]
    rs2 = REGISTER_MAP[parts[3]]

    info = OPCODE_TABLE[instr]

    return (
        info["funct7"] +
        rs2 +
        rs1 +
        info["funct3"] +
        rd +
        info["opcode"]
    )


def encode_I(parts):
    instr = parts[0]
    info = OPCODE_TABLE[instr]

    rd = REGISTER_MAP[parts[1]]

    if instr == "lw":
        # lw x1, 0(x2)
        imm, rs1 = parts[2].split("(")
        rs1 = rs1.replace(")", "")
        rs1 = REGISTER_MAP[rs1]
    else:
        rs1 = REGISTER_MAP[parts[2]]
        imm = parts[3]

    imm_bin = to_binary(imm, 12)

    return (
        imm_bin +
        rs1 +
        info["funct3"] +
        rd +
        info["opcode"]
    )


def encode_S(parts):
    instr = parts[0]
    info = OPCODE_TABLE[instr]

    rs2 = REGISTER_MAP[parts[1]]
    imm, rs1 = parts[2].split("(")
    rs1 = rs1.replace(")", "")
    rs1 = REGISTER_MAP[rs1]

    imm_bin = to_binary(imm, 12)

    return (
        imm_bin[:7] +
        rs2 +
        rs1 +
        info["funct3"] +
        imm_bin[7:] +
        info["opcode"]
    )


def encode_B(parts, pc, symbol_table):
    instr = parts[0]
    info = OPCODE_TABLE[instr]

    rs1 = REGISTER_MAP[parts[1]]
    rs2 = REGISTER_MAP[parts[2]]

    label = parts[3]
    target = symbol_table[label]

    offset = target - pc
    imm_bin = to_binary(offset, 13)

    return (
        imm_bin[0] +
        imm_bin[2:8] +
        rs2 +
        rs1 +
        info["funct3"] +
        imm_bin[8:12] +
        imm_bin[1] +
        info["opcode"]
    )


def encode_U(parts):
    instr = parts[0]
    info = OPCODE_TABLE[instr]

    rd = REGISTER_MAP[parts[1]]
    imm = to_binary(parts[2], 20)

    return imm + rd + info["opcode"]


def encode_J(parts, pc, symbol_table):
    instr = parts[0]
    info = OPCODE_TABLE[instr]

    rd = REGISTER_MAP[parts[1]]
    label = parts[2]

    target = symbol_table[label]
    offset = target - pc

    imm_bin = to_binary(offset, 21)

    return (
        imm_bin[0] +
        imm_bin[10:20] +
        imm_bin[9] +
        imm_bin[1:9] +
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
            continue

        parts = line.replace(",", "").split()
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
