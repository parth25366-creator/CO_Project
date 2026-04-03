# Hard Test 4: LUI + ADDI large constant & nested loop
lui t0, 1
addi t0, t0, -1
addi t1, zero, 2
addi t2, zero, 0
outer: addi t2, t2, 1
addi t3, zero, 0
inner: addi t3, t3, 1
blt t3, t1, inner
blt t2, t1, outer
beq zero, zero, 0
