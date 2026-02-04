import sys
import re

# REGISTER ENCODING

REGISTERS = {
    "zero":0,"ra":1,"sp":2,"gp":3,"tp":4,
    "t0":5,"t1":6,"t2":7,
    "s0":8,"fp":8,"s1":9,
    "a0":10,"a1":11,"a2":12,"a3":13,"a4":14,"a5":15,"a6":16,"a7":17,
    "s2":18,"s3":19,"s4":20,"s5":21,"s6":22,"s7":23,"s8":24,"s9":25,"s10":26,"s11":27,
    "t3":28,"t4":29,"t5":30,"t6":31
}


# HELPER FUNCTIONS

def error(msg, line):
    print(f"Error at line {line}: {msg}")
    sys.exit()

def to_bin(val, bits):
    if val < 0:
        val = (1 << bits) + val
    return format(val, f'0{bits}b')

def reg_bin(r, line):
    if r not in REGISTERS:
        error("Invalid register", line)
    return to_bin(REGISTERS[r], 5)


# OPCODE TABLES

R_TYPE = {
    "add":("0000000","000"),
    "sub":("0100000","000"),
    "sll":("0000000","001"),
    "slt":("0000000","010"),
    "sltu":("0000000","011"),
    "xor":("0000000","100"),
    "srl":("0000000","101"),
    "or":("0000000","110"),
    "and":("0000000","111")
}

I_TYPE = {
    "addi":"000",
    "sltiu":"011",
    "jalr":"000",
    "lw":"010"
}

S_TYPE = {"sw":"010"}

B_TYPE = {
    "beq":"000","bne":"001","blt":"100",
    "bge":"101","bltu":"110","bgeu":"111"
}

U_TYPE = {"lui":"0110111","auipc":"0010111"}
J_TYPE = {"jal":"1101111"}


# PARSE HELPERS

def parse_offset(token):
    # matches 12(rs1)
    m = re.match(r'(-?\d+)\((\w+)\)', token)
    if not m:
        return None
    return int(m.group(1)), m.group(2)


# ENCODERS


def encode_R(op, rd, rs1, rs2, line):
    funct7, funct3 = R_TYPE[op]
    return (
        funct7 +
        reg_bin(rs2,line) +
        reg_bin(rs1,line) +
        funct3 +
        reg_bin(rd,line) +
        "0110011"
    )

def encode_I(op, rd, rs1, imm, line):
    funct3 = I_TYPE[op]
    opcode = "0010011" if op!="jalr" and op!="lw" else ("1100111" if op=="jalr" else "0000011")
    return (
        to_bin(imm,12) +
        reg_bin(rs1,line) +
        funct3 +
        reg_bin(rd,line) +
        opcode
    )

def encode_S(op, rs2, rs1, imm, line):
    funct3 = S_TYPE[op]
    imm_bin = to_bin(imm,12)
    return (
        imm_bin[:7] +
        reg_bin(rs2,line) +
        reg_bin(rs1,line) +
        funct3 +
        imm_bin[7:] +
        "0100011"
    )

def encode_B(op, rs1, rs2, imm, line):
    funct3 = B_TYPE[op]
    imm_bin = to_bin(imm,13)
    return (
        imm_bin[0] +
        imm_bin[2:8] +
        reg_bin(rs2,line) +
        reg_bin(rs1,line) +
        funct3 +
        imm_bin[8:12] +
        imm_bin[1] +
        "1100011"
    )

def encode_U(op, rd, imm, line):
    opcode = U_TYPE[op]
    return to_bin(imm,20) + reg_bin(rd,line) + opcode

def encode_J(op, rd, imm, line):
    imm_bin = to_bin(imm,21)
    return (
        imm_bin[0] +
        imm_bin[10:20] +
        imm_bin[9] +
        imm_bin[1:9] +
        reg_bin(rd,line) +
        "1101111"
    )


# MAIN FUNCTION

def main():

    if len(sys.argv) < 3:
        sys.exit()

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file) as f:
        lines = f.readlines()

    # PASS 1: LABEL COLLECTION
    labels = {}
    instructions = []
    pc = 0

    for idx, raw in enumerate(lines):
        line = raw.strip()
        if not line:
            continue

        if ":" in line:
            label, rest = line.split(":")
            labels[label.strip()] = pc
            line = rest.strip()
            if not line:
                continue

        instructions.append((line, idx+1))
        pc += 4

    # Virtual halt check
    if instructions[-1][0].replace(" ","") != "beqzero,zero,0":
        error("Missing or invalid Virtual Halt", instructions[-1][1])

    ########################################################

    pc = 0
    binary = []

    for inst, line_no in instructions:

        tokens = [t.strip() for t in re.split(r'[,\s]+', inst)]
        op = tokens[0]

        try:
            # R TYPE
            if op in R_TYPE:
                binary.append(encode_R(op,tokens[1],tokens[2],tokens[3],line_no))

            # I TYPE (addi/sltiu/jalr)
            elif op in ["addi","sltiu","jalr"]:
                binary.append(encode_I(op,tokens[1],tokens[2],int(tokens[3]),line_no))

            # LW
            elif op == "lw":
                imm, rs1 = parse_offset(tokens[2])
                binary.append(encode_I(op,tokens[1],rs1,imm,line_no))

            # SW
            elif op == "sw":
                imm, rs1 = parse_offset(tokens[2])
                binary.append(encode_S(op,tokens[1],rs1,imm,line_no))

            # BRANCH
            elif op in B_TYPE:
                label = tokens[3]
                if label not in labels:
                    error("Undefined label", line_no)
                offset = labels[label] - pc
                binary.append(encode_B(op,tokens[1],tokens[2],offset,line_no))

            # U TYPE
            elif op in U_TYPE:
                binary.append(encode_U(op,tokens[1],int(tokens[2]),line_no))

            # J TYPE
            elif op == "jal":
                label = tokens[2]
                if label not in labels:
                    error("Undefined label", line_no)
                offset = labels[label] - pc
                binary.append(encode_J(op,tokens[1],offset,line_no))

            else:
                error("Invalid instruction", line_no)

        except:
            error("Syntax error", line_no)

        pc += 4

    ########################################################

    with open(output_file,"w") as f:
        for b in binary:
            f.write(b+"\n")

if __name__ == "__main__":
    main()
