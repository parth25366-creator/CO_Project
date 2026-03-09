
import os
import sys


def fail(message):
    print(message)
    sys.exit(1)


regs = {
    "x0":  "00000", "x1":  "00001", "x2":  "00010", "x3":  "00011",
    "x4":  "00100", "x5":  "00101", "x6":  "00110", "x7":  "00111",
    "x8":  "01000", "x9":  "01001", "x10": "01010", "x11": "01011",
    "x12": "01100", "x13": "01101", "x14": "01110", "x15": "01111",
    "x16": "10000", "x17": "10001", "x18": "10010", "x19": "10011",
    "x20": "10100", "x21": "10101", "x22": "10110", "x23": "10111",
    "x24": "11000", "x25": "11001", "x26": "11010", "x27": "11011",
    "x28": "11100", "x29": "11101", "x30": "11110", "x31": "11111",

    
    "zero": "00000", "ra": "00001", "sp": "00010", "gp": "00011", "tp": "00100",
    "fp": "01000", "t0": "00101", "t1": "00110", "t2": "00111", "t3": "11100", 
    "t4": "11101", "t5": "11110", "t6": "11111", "s0": "01000", "s1": "01001",
    "s2": "10010", "s3": "10011", "s4": "10100", "s5": "10101", "s6": "10110", 
    "s7": "10111", "s8": "11000", "s9": "11001", "s10": "11010", "s11": "11011", 
    "a0": "01010", "a1": "01011", "a2": "01100", "a3": "01101", "a4": "01110", 
    "a5": "01111", "a6": "10000", "a7": "10001"
}

InstrucnTypes = {

    #r
    "add": "R", "sub": "R", "sll": "R", 
    "slt": "R", "sltu": "R", "xor": "R", 
    "srl": "R", "or":  "R", "and": "R",

    #i
    "lw": "I", "addi": "I",
    "sltiu": "I", "jalr": "I",

    #s
    "sw": "S",

    #b
    "beq":  "B", "bne":  "B",
    "blt":  "B", "bge":  "B",
    "bltu": "B", "bgeu": "B",

    # u
    "lui":   "U", "auipc": "U",

    #j
    "jal": "J"
}


Opcodes = {

    #r
    "add": "0110011",    "sub" : "0110011",   "sll": "0110011",
    "slt": "0110011",    "sltu": "0110011",   "xor": "0110011",
    "srl": "0110011",    "or"  : "0110011",   "and": "0110011",

    #i
    "lw":  "0000011", "addi":  "0010011", "sltiu": "0010011", "jalr":  "1100111",

    #s
    "sw": "0100011",

    #b
    "beq" :  "1100011", "bne":  "1100011","blt":  "1100011",
    "bge":  "1100011", "bltu": "1100011","bgeu": "1100011",

    #u
    "lui": "0110111", "auipc": "0010111",

    #j
    "jal": "1101111"
}


funct3 = {

    # r
    "add":  "000","sub":  "000","sll":  "001","slt":  "010","sltu": "011"
    ,"xor":  "100","srl":  "101","or": "110","and":  "111",

    #i
    "lw":    "010","addi":  "000",
    "sltiu": "011","jalr":  "000",

    #s
    "sw": "010",

    #b
    "beq":  "000","bne":  "001","blt":  "100",
    "bge":  "101","bltu": "110","bgeu": "111"
}



funct7 = {
    "add": "0000000", "sub" : "0100000", "sll": "0000000", 
    "slt": "0000000", "sltu": "0000000", "xor": "0000000", 
    "srl": "0000000", "or": "0000000", "and": "0000000"
}


def convertBinary(value, bits):
    if value < 0:
        value = (1 << bits) + value
    return format(value, "0" + str(bits) + "b")


def splitting_memory_operand(text, op_name):
    left = text.find("(")
    right = text.find(")")

    if left == -1 or right == -1 or right < left:
        fail("invalid format for " + op_name)

    imm = text[:left]
    rs1 = text[left + 1:right]
    return imm, rs1


def ConvertRType(parts):
    if len(parts) != 4:
        fail("format not valid")

    instruction = parts[0]

    fn7 = funct7[instruction]
    fn3 = funct3[instruction]
    opcode = Opcodes[instruction]

    rd_name = parts[1].strip()
    rs1_name = parts[2].strip()
    rs2_name = parts[3].strip()

    rs2 = regs[rs2_name]
    rs1 = regs[rs1_name]
    rd = regs[rd_name]

    if (rd_name not in regs) or (rs1_name not in regs) or (rs2_name not in regs):
        fail("register is not valid")

    binary = fn7 + rs2 + rs1 + fn3 + rd + opcode

    return binary


def ConvertIType(parts):
    instruction = parts[0]

    if instruction == "addi" or instruction == "sltiu":
        if len(parts) != 4:
            fail("invalid format for ", instruction)

        rd = parts[1]
        rs1 = parts[2]
        imm = parts[3]
        func3=funct3[instruction]
        opcode=Opcodes[instruction]

        if rd not in regs or rs1 not in regs:
            fail("register invalid")

        imm_binary = convertBinary(int(imm), 12)
        return imm_binary + regs[rs1] + func3 + regs[rd] + opcode

    if instruction == "lw":
        if len(parts) != 3:
            fail("format not valid for lw")

        rd = parts[1]
        imm_text, rs1 = splitting_memory_operand(parts[2], "lw")
        func3=funct3[instruction]
        opcode=Opcodes[instruction]

        if rd not in regs or rs1 not in regs:
            fail("register invalid")

        imm_binary = convertBinary(int(imm_text), 12)
        return imm_binary + regs[rs1] +func3 + regs[rd] + opcode

    if instruction == "jalr":
        if len(parts) != 4:
            fail("format not valid for jalr")

        rd = parts[1]
        rs1 = parts[2]
        imm = parts[3]
        func3=funct3[instruction]
        opcode=Opcodes[instruction]

        if rd not in regs or rs1 not in regs:
            fail("invalid register")

        imm_binary = convertBinary(int(imm), 12)
        return imm_binary + regs[rs1] + func3 + regs[rd] + opcode

    fail("i-type instruction isn't supported")


def ConvertSType(parts):
    if len(parts) != 3:
        fail("invalid format for sw")

    instruction = parts[0]
    rs2_name = parts[1]
    imm_text, rs1_name = splitting_memory_operand(parts[2], "sw")

    if (rs2_name not in regs) or (rs1_name not in regs):
        fail("invalid register")

    imm_binary = convertBinary(int(imm_text), 12)
    rs2 = regs[rs2_name]
    rs1 = regs[rs1_name]
    fn3 = funct3[instruction]
    opcode = Opcodes[instruction]

    binary = imm_binary[0:7] + rs2 + rs1 + fn3 + imm_binary[7:12] + opcode
    
    return binary

def ConvertBType(parts, pc, labels):
    if len(parts) != 4:
        fail("invalid format for branch")

    instruction = parts[0]
    rs1_name = parts[1]
    rs2_name = parts[2]
    target = parts[3]

    if rs1_name not in regs or rs2_name not in regs:
        fail("invalid register")

    if target in labels:
        offset = labels[target] - pc
    else:
        offset = int(target)

    if (offset % 2 != 0):
        fail("jump not aligned")

    imm = convertBinary(offset, 13)
    imm12 = imm[0]
    imm11 = imm[1]
    imm10_5 = imm[2:8]
    imm4_1 = imm[8:12]
    opcode = Opcodes[instruction]
    fn3 = funct3[instruction]

    binary = imm12 + imm10_5 + regs[rs2_name] + regs[rs1_name] + fn3 + imm4_1 + imm11 + opcode
    
    return binary

def ConvertJType(parts, pc, labels):
    if len(parts) != 3:
        fail("invalid format for jal")

    instruction = parts[0]
    rd_name = parts[1]
    label = parts[2]

    if rd_name not in regs:
        fail("invalid register")

    if label not in labels:
        fail("label isn't defined")

    offset = labels[label] - pc

    if offset % 2 != 0:
        fail("jump not aligned")

    imm = convertBinary(offset, 21)
    imm20 = imm[0]
    imm19_12 = imm[1:9]
    imm11 = imm[9]
    imm10_1 = imm[10:20]
    opcode = Opcodes[instruction]

    binary = imm20 + imm10_1 + imm11 + imm19_12 + regs[rd_name] + opcode

    return binary

def ConvertUType(parts):
    if len(parts) != 3:
        fail("invalid format for U-type")

    instruction = parts[0]
    rd_name = parts[1]
    imm_text = parts[2]
    opcode = Opcodes[instruction]

    if rd_name not in regs:
        fail("invalid register")
        

    if imm_text.startswith("0x"):
        imm_value = int(imm_text, 16)
    else:
        imm_value = int(imm_text)

    imm_binary = convertBinary(imm_value, 20)
    binary = imm_binary + regs[rd_name] + opcode

    return binary

def Pass1(lines):
    labels = {}
    pc = 0
    line_number = 1

    for line in lines:
        line = line.strip()

        if line == "":
            line_number += 1
            continue

        if ":" in line:
            label = line.split(":")[0]

            if label in labels:
                fail("Error detected at line " + str(line_number) + ": duplicate label")

            labels[label] = pc

            if line.endswith(":"):
                line_number += 1
                continue

        pc += 4
        line_number += 1

    return labels


def main():
    if len(sys.argv) < 3:
        fail("usage: python3 Assembler.py <input_file> <output_file>")

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, "r") as file_handle:
        lines = file_handle.readlines()

    labels = Pass1(lines)

    pc = 0
    line_number = 1
    output = []

    for line in lines:
        line = line.strip()

        if line == "" or line.endswith(":"):
            line_number += 1
            continue

        line = line.replace(",", " ")

        if ":" in line:
            split_line = line.split(":", 1)
            rest = split_line[1].strip()
            if rest == "":
                line_number += 1
                continue
            line = rest

        parts = line.split()
        instruction = parts[0]

        if instruction not in InstrucnTypes:
            fail("error at line " + str(line_number) + ": invalid instruction")

        inst_type = InstrucnTypes[instruction]

        if inst_type == "R":
            binary = ConvertRType(parts)
        elif inst_type == "I":
            binary = ConvertIType(parts)
        elif inst_type == "S":
            binary = ConvertSType(parts)
        elif inst_type == "B":
            binary = ConvertBType(parts, pc, labels)
        elif inst_type == "U":
            binary = ConvertUType(parts)
        elif inst_type == "J":
            binary = ConvertJType(parts, pc, labels)
        else:
            fail("instruction type NOT supported!")

        output.append(binary)
        pc += 4
        line_number += 1

    out_dir = os.path.dirname(output_file)
    if out_dir != "":
        os.makedirs(out_dir, exist_ok=True)

    with open(output_file, "w") as file_handle:
        for binary_line in output:
            file_handle.write(binary_line + "\n")


if __name__ == "__main__":
    main()
