import sys

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 Assembler.py <input_file> <output_file>")
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, 'r') as f:
        lines = f.readlines()

    with open(output_file, 'w') as f:
        for line in lines:
            line = line.strip()
            if line == "":
                continue
            f.write("00000000000000000000000000000000\n")

    print("Dummy assembler executed successfully.")

if __name__ == "__main__":
    main()
