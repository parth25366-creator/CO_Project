# Hard Test 8: All 6 B-type instructions
addi t0, zero, 5
addi t1, zero, 3
addi t2, zero, 5
beq t0, t2, l1
addi a0, zero, 1
l1: bne t0, t1, l2
addi a0, zero, 2
l2: blt t1, t0, l3
addi a0, zero, 3
l3: bge t0, t1, l4
addi a0, zero, 4
l4: bltu t1, t0, l5
addi a0, zero, 5
l5: bgeu t0, t1, done
addi a0, zero, 6
done: addi a1, zero, 99
beq zero, zero, 0
