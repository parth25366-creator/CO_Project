import sys
import re

R_TYPE = {
    "add":  {"opcode": "0110011", "funct3": "000", "funct7": "0000000"},
    "sub":  {"opcode": "0110011", "funct3": "000", "funct7": "0100000"},
    "sll":  {"opcode": "0110011", "funct3": "001", "funct7": "0000000"},
    "slt":  {"opcode": "0110011", "funct3": "010", "funct7": "0000000"},
    "sltu": {"opcode": "0110011", "funct3": "011", "funct7": "0000000"},
    "xor":  {"opcode": "0110011", "funct3": "100", "funct7": "0000000"},
    "srl":  {"opcode": "0110011", "funct3": "101", "funct7": "0000000"},
    "or":   {"opcode": "0110011", "funct3": "110", "funct7": "0000000"},
    "and":  {"opcode": "0110011", "funct3": "111", "funct7": "0000000"}
}

I_TYPE = {
    "lw":    {"opcode": "0000011", "funct3": "010"},
    "addi":  {"opcode": "0010011", "funct3": "000"},
    "sltiu": {"opcode": "0010011", "funct3": "011"},
    "jalr":  {"opcode": "1100111", "funct3": "000"}
}

S_TYPE = {"sw": {"opcode": "0100011", "funct3": "010"}}

B_TYPE = {
    "beq":  {"opcode": "1100011", "funct3": "000"},
    "bne":  {"opcode": "1100011", "funct3": "001"},
    "blt":  {"opcode": "1100011", "funct3": "100"},
    "bge":  {"opcode": "1100011", "funct3": "101"},
    "bltu": {"opcode": "1100011", "funct3": "110"},
    "bgeu": {"opcode": "1100011", "funct3": "111"}
}

U_TYPE = {
    "lui":   {"opcode": "0110111"},
    "auipc": {"opcode": "0010111"}
}

J_TYPE = {"jal": {"opcode": "1101111"}}

REGISTERS = {
    "zero": "00000", "ra": "00001", "sp": "00010", "gp": "00011", "tp": "00100",
    "t0": "00101", "t1": "00110", "t2": "00111", "s0": "01000", "fp": "01000",
    "s1": "01001", "a0": "01010", "a1": "01011", "a2": "01100", "a3": "01101",
    "a4": "01110", "a5": "01111", "a6": "10000", "a7": "10001", "s2": "10010",
    "s3": "10011", "s4": "10100", "s5": "10101", "s6": "10110", "s7": "10111",
    "s8": "11000", "s9": "11001", "s10": "11010", "s11": "11011", "t3": "11100",
    "t4": "11101", "t5": "11110", "t6": "11111"
}

def to_bin(val, bits, line_num):
    """Converts int to 2's complement binary, enforcing bit length bounds."""
    min_val = -(1 << (bits - 1))
    max_val = (1 << (bits - 1)) - 1
    if not (min_val <= val <= max_val):
        print(f"Error on line {line_num}: Immediate {val} goes out of bounds for {bits}-bit size.")
        sys.exit(1)
    if val < 0:
        val = (1 << bits) + val
    return bin(val)[2:].zfill(bits)

def parse_mem_operand(operand):
    """Extracts immediate and register from syntax like 'offset(rs1)'."""
    match = re.match(r"(-?\d+)\((.+)\)", operand)
    if match:
        return int(match.group(1)), match.group(2).strip()
    return None, None

def check_reg(reg, line_num):
    """Validates the ABI register name[cite: 133]."""
    if reg not in REGISTERS:
        print(f"Error on line {line_num}: Typo or illegal register name '{reg}'.")
        sys.exit(1)
    return REGISTERS[reg]

def assemble(input_file, output_file):
    try:
        with open(input_file, 'r') as f:
            raw_lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: Could not find input file '{input_file}'.")
        sys.exit(1)

    lines = []
    for num, line in enumerate(raw_lines, 1):
        line = line.split('#')[0].strip() 
        if line:
            lines.append((num, line))

    if not lines:
        print("Error: Input file is empty.")
        sys.exit(1)
 
    last_line = lines[-1][1].replace(" ", "")
    if last_line not in ["beqzero,zero,0x00000000", "beqzero,zero,0"]:
        print(f"Error: Missing or misplaced Virtual Halt at the end of the program.")
        sys.exit(1)

    labels = {}
    instructions = []
     
    pc = 0
    for original_line_num, line in lines:
        if ":" in line:
            label_part, instr_part = line.split(":", 1)
            label = label_part.strip()
            if not label[0].isalpha():
                print(f"Error on line {original_line_num}: Label '{label}' must start with a character.")
                sys.exit(1)
            labels[label] = pc
            if instr_part.strip():
                instructions.append((pc, instr_part.strip(), original_line_num))
                pc += 4
        else:
            instructions.append((pc, line, original_line_num))
            pc += 4

    binary_output = []
    for pc, instr, line_num in instructions:
         
        if instr.replace(" ", "") in ["beqzero,zero,0x00000000", "beqzero,zero,0"]:
            binary_output.append("00000000000000000000000001100011")
            continue
            
        parts = instr.replace(',', ' ').split()
        mnemonic = parts[0]

        try:
            if mnemonic in R_TYPE:
                
                rd, rs1, rs2 = parts[1], parts[2], parts[3]
                op = R_TYPE[mnemonic]
                binary_output.append(f"{op['funct7']}{check_reg(rs2, line_num)}{check_reg(rs1, line_num)}{op['funct3']}{check_reg(rd, line_num)}{op['opcode']}")

            elif mnemonic in I_TYPE:
                op = I_TYPE[mnemonic]
                if mnemonic == "lw":
                    
                    rd = parts[1]
                    imm, rs1 = parse_mem_operand(parts[2])
                    b_imm = to_bin(imm, 12, line_num)
                    binary_output.append(f"{b_imm}{check_reg(rs1, line_num)}{op['funct3']}{check_reg(rd, line_num)}{op['opcode']}")
                else:
                   
                    rd, rs1, imm = parts[1], parts[2], parts[3]
                    b_imm = to_bin(int(imm), 12, line_num)
                    binary_output.append(f"{b_imm}{check_reg(rs1, line_num)}{op['funct3']}{check_reg(rd, line_num)}{op['opcode']}")

            elif mnemonic in S_TYPE:
            
                op = S_TYPE[mnemonic]
                rs2 = parts[1]
                imm, rs1 = parse_mem_operand(parts[2])
                b_imm = to_bin(imm, 12, line_num)
                binary_output.append(f"{b_imm[:7]}{check_reg(rs2, line_num)}{check_reg(rs1, line_num)}{op['funct3']}{b_imm[7:]}{op['opcode']}")

            elif mnemonic in B_TYPE:
                
                op = B_TYPE[mnemonic]
                rs1, rs2, target = parts[1], parts[2], parts[3]
                
                offset = labels[target] - pc if target in labels else int(target)
                b_imm = to_bin(offset, 13, line_num) 
                
                
                b_str = f"{b_imm[0]}{b_imm[2:8]}{check_reg(rs2, line_num)}{check_reg(rs1, line_num)}{op['funct3']}{b_imm[8:12]}{b_imm[1]}{op['opcode']}"
                binary_output.append(b_str)

            elif mnemonic in U_TYPE:
                
                op = U_TYPE[mnemonic]
                rd, imm = parts[1], parts[2]
                b_imm = to_bin(int(imm), 32, line_num)[:20] 
                binary_output.append(f"{b_imm}{check_reg(rd, line_num)}{op['opcode']}")

            elif mnemonic in J_TYPE:
                
                op = J_TYPE[mnemonic]
                rd, target = parts[1], parts[2]
                
                offset = labels[target] - pc if target in labels else int(target)
                b_imm = to_bin(offset, 21, line_num) 
                
                b_str = f"{b_imm[0]}{b_imm[10:20]}{b_imm[9]}{b_imm[1:9]}{check_reg(rd, line_num)}{op['opcode']}"
                binary_output.append(b_str)

            else:
                print(f"Error on line {line_num}: Unsupported or illegal instruction '{mnemonic}'.")
                sys.exit(1)

        except (IndexError, ValueError) as e:
            print(f"Error on line {line_num}: Syntax error or invalid operand format.")
            sys.exit(1)

    with open(output_file, 'w') as f:
        for b in binary_output:
            f.write(b + '\n')
            
    print("Assembly successful.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python assembler.py <input.s> <output.txt>")
        sys.exit(1)
    assemble(sys.argv[1], sys.argv[2])



