import sys
import re

REGISTER_MAP={
"zero":"00000","ra":"00001","sp":"00010","gp":"00011","tp":"00100",
"t0":"00101","t1":"00110","t2":"00111","s0":"01000","fp":"01000",
"s1":"01001","a0":"01010","a1":"01011","a2":"01100","a3":"01101",
"a4":"01110","a5":"01111","a6":"10000","a7":"10001","s2":"10010",
"s3":"10011","s4":"10100","s5":"10101","s6":"10110","s7":"10111",
"s8":"11000","s9":"11001","s10":"11010","s11":"11011","t3":"11100",
"t4":"11101","t5":"11110","t6":"11111"
}

R_TYPE={
"add":("0000000","000","0110011"),
"sub":("0100000","000","0110011"),
"sll":("0000000","001","0110011"),
"slt":("0000000","010","0110011"),
"xor":("0000000","100","0110011"),
"srl":("0000000","101","0110011"),
"or":("0000000","110","0110011"),
"and":("0000000","111","0110011")
}

I_TYPE={"addi":("000","0010011"),"lw":("010","0000011"),"jalr":("000","1100111")}
S_TYPE={"sw":("010","0100011")}
B_TYPE={"beq":("000","1100011"),"bne":("001","1100011")}

def to_binary(v,b):
    if v<0:v=(1<<b)+v
    return format(v,f'0{b}b')[-b:]

def extract_instruction(l):
    if ":" in l:return l.split(":",1)[1].strip()
    return l.strip()

def normalize(i):
    return i.replace(" ","").lower()

def error(msg,outfile):
    with open(outfile,"w") as f:
        f.write(msg+"\n")
    sys.exit()

def validate_virtual_halt(lines,outfile):
    insts=[]
    nums=[]
    for i,l in enumerate(lines):
        l=l.strip()
        if not l:continue
        ins=extract_instruction(l)
        if ins:
            insts.append(ins)
            nums.append(i+1)

    halt="beqzero,zero,0"
    norm=[normalize(x) for x in insts]

    if halt not in norm:
        error(f"Error at line {nums[-1]}: Missing or invalid Virtual Halt",outfile)

    for i in range(len(norm)-1):
        if norm[i]==halt:
            error(f"Error at line {nums[i]}: Virtual Halt not last instruction",outfile)

    if norm[-1]!=halt:
        error(f"Error at line {nums[-1]}: Missing or invalid Virtual Halt",outfile)

def collect_labels(lines):
    labels={}
    pc=0
    for l in lines:
        c=l.strip()
        if not c:continue
        if ":" in c:
            lab=c.split(":")[0].strip()
            labels[lab]=pc
            if c.endswith(":"):continue
        pc+=4
    return labels

def encode_r(op,rd,rs1,rs2):
    f7,f3,opc=R_TYPE[op]
    return f7+REGISTER_MAP[rs2]+REGISTER_MAP[rs1]+f3+REGISTER_MAP[rd]+opc

def encode_i(op,rd,rs1,imm):
    f3,opc=I_TYPE[op]
    ib=to_binary(int(imm),12)
    return ib+REGISTER_MAP[rs1]+f3+REGISTER_MAP[rd]+opc

def encode_s(op,rs1,rs2,imm):
    f3,opc=S_TYPE[op]
    ib=to_binary(int(imm),12)
    return ib[:7]+REGISTER_MAP[rs2]+REGISTER_MAP[rs1]+f3+ib[7:]+opc

def encode_b(op,rs1,rs2,imm):
    f3,opc=B_TYPE[op]
    ib=to_binary(int(imm),13)
    return ib[0]+ib[2:8]+REGISTER_MAP[rs2]+REGISTER_MAP[rs1]+f3+ib[8:12]+ib[1]+opc

def assemble(lines,outfile):
    validate_virtual_halt(lines,outfile)
    labels=collect_labels(lines)
    pc=0
    out=[]

    for ln,l in enumerate(lines,start=1):
        l=l.strip()
        if not l:continue
        ins=extract_instruction(l)
        if not ins:continue
        p=re.split(r'[,\s()]+',ins)
        op=p[0]

        try:
            if op in R_TYPE:
                rd,rs1,rs2=p[1:4]
                b=encode_r(op,rd,rs1,rs2)

            elif op in I_TYPE and op!="lw":
                rd,rs1,imm=p[1:4]
                b=encode_i(op,rd,rs1,imm)

            elif op=="lw":
                rd,imm,rs1=p[1:4]
                b=encode_i(op,rd,rs1,imm)

            elif op=="sw":
                rs2,imm,rs1=p[1:4]
                b=encode_s(op,rs1,rs2,imm)

            elif op in B_TYPE:
                rs1,rs2,target=p[1:4]

                if re.match(r'^-?\d+$',target):
                    off=int(target)
                else:
                    if target not in labels:
                        error(f"Error at line {ln}: Undefined label",outfile)
                    off=labels[target]-pc

                b=encode_b(op,rs1,rs2,off)

            else:
                error(f"Error at line {ln}: Invalid instruction",outfile)

            out.append(b)
            pc+=4

        except:
            error(f"Error at line {ln}: Invalid syntax",outfile)

    return out

def main():
    input_file=sys.argv[1]
    output_file=sys.argv[2]

    with open(input_file,"r") as f:
        lines=f.readlines()

    machine=assemble(lines,output_file)

    with open(output_file,"w") as f:
        for m in machine:
            f.write(m+"\n")

if __name__=="__main__":
    main()
