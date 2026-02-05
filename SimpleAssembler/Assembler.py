import sys

REGISTER_MAP={
"x0":"00000","zero":"00000",
"x1":"00001","ra":"00001",
"x2":"00010","sp":"00010",
"x3":"00011","gp":"00011",
"x4":"00100","tp":"00100",
"x5":"00101","t0":"00101",
"x6":"00110","t1":"00110",
"x7":"00111","t2":"00111",
"x8":"01000","s0":"01000","fp":"01000",
"x9":"01001","s1":"01001",
"x10":"01010","a0":"01010",
"x11":"01011","a1":"01011",
"x12":"01100","a2":"01100",
"x13":"01101","a3":"01101",
"x14":"01110","a4":"01110",
"x15":"01111","a5":"01111",
"x16":"10000","a6":"10000",
"x17":"10001","a7":"10001",
"x18":"10010","s2":"10010",
"x19":"10011","s3":"10011",
"x20":"10100","s4":"10100",
"x21":"10101","s5":"10101",
"x22":"10110","s6":"10110",
"x23":"10111","s7":"10111",
"x24":"11000","s8":"11000",
"x25":"11001","s9":"11001",
"x26":"11010","s10":"11010",
"x27":"11011","s11":"11011",
"x28":"11100","t3":"11100",
"x29":"11101","t4":"11101",
"x30":"11110","t5":"11110",
"x31":"11111","t6":"11111"
}

R_TYPE={
"add":("000","0000000","0110011"),
"sub":("000","0100000","0110011"),
"and":("111","0000000","0110011"),
"or":("110","0000000","0110011"),
"slt":("010","0000000","0110011")
}

I_TYPE={
"addi":("000","0010011"),
"lw":("010","0000011"),
"jalr":("000","1100111")
}

S_TYPE={
"sw":("010","0100011")
}

B_TYPE={
"beq":("000","1100011"),
"bne":("001","1100011"),
"blt":("100","1100011"),
"bge":("101","1100011")
}

HALT_CODE="00000000000000000000000001100011"


def to_binary(n,bits):
    if n<0:
        n=(1<<bits)+n
    return format(n,'0{}b'.format(bits))


def error(msg,line):
    print(f"Error at line {line+1}: {msg}")
    sys.exit(0)


def encode_r(op,rd,rs1,rs2):
    funct3,funct7,opcode=R_TYPE[op]
    return funct7+REGISTER_MAP[rs2]+REGISTER_MAP[rs1]+funct3+REGISTER_MAP[rd]+opcode


def encode_i(op,rd,rs1,imm):
    funct3,opcode=I_TYPE[op]
    imm=to_binary(int(imm),12)
    return imm+REGISTER_MAP[rs1]+funct3+REGISTER_MAP[rd]+opcode


def encode_s(op,rs1,rs2,imm):
    funct3,opcode=S_TYPE[op]
    imm=to_binary(int(imm),12)
    return imm[:7]+REGISTER_MAP[rs2]+REGISTER_MAP[rs1]+funct3+imm[7:]+opcode


def encode_b(op,rs1,rs2,offset):
    funct3,opcode=B_TYPE[op]
    offset//=2
    imm=to_binary(offset,13)

    return (
        imm[0]+
        imm[2:8]+
        REGISTER_MAP[rs2]+
        REGISTER_MAP[rs1]+
        funct3+
        imm[8:12]+
        imm[1]+
        opcode
    )


def preprocess(lines):
    clean=[]
    labels={}
    pc=0

    for i,line in enumerate(lines):
        line=line.strip()
        if not line:
            continue

        if ":" in line:
            label,rest=line.split(":",1)
            labels[label.strip()]=pc
            line=rest.strip()
            if not line:
                continue

        clean.append((i,line))
        pc+=4

    return clean,labels


def tokenize(line):
    line=line.replace(",", " ")
    line=line.replace("(", " ")
    line=line.replace(")", " ")
    return line.split()


def assemble(clean,labels):
    output=[]
    pc=0
    halt_found=False

    for idx,line in clean:
        p=tokenize(line)
        op=p[0]

        if op in R_TYPE:
            rd,rs1,rs2=p[1:4]
            b=encode_r(op,rd,rs1,rs2)

        elif op in I_TYPE:
            if op=="lw":
                rd=p[1]
                imm=p[2]
                rs1=p[3]
                b=encode_i(op,rd,rs1,imm)
            else:
                rd,rs1,imm=p[1:4]
                b=encode_i(op,rd,rs1,imm)

        elif op in S_TYPE:
            rs2,imm,rs1=p[1:4]
            b=encode_s(op,rs1,rs2,imm)

        elif op in B_TYPE:
            rs1,rs2,target=p[1:4]

            if target not in labels:
                error("Undefined label",idx)

            off=labels[target]-pc
            b=encode_b(op,rs1,rs2,off)

            if rs1=="zero" and rs2=="zero" and off==0:
                halt_found=True
                if pc!=(len(clean)-1)*4:
                    error("Virtual Halt not last instruction",idx)

        else:
            error("Invalid syntax",idx)

        output.append(b)
        pc+=4

    if not halt_found:
        error("Missing Virtual Halt",clean[-1][0])

    return output


def main():
    lines=sys.stdin.readlines()
    clean,labels=preprocess(lines)
    machine=assemble(clean,labels)

    for m in machine:
        print(m)


if __name__=="__main__":
    main()
