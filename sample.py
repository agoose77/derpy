no_of_lines = 5
lines = ""
for i in xrange(5):

    lines += input()+"\n"
    a=raw_input("if u want to continue (Y/n)")
    ""
    if(a=='y'):
        continue
    else:
        break
    print(lines)