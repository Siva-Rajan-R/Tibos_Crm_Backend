alphabets='abcdefghijklmnopqrstuvwxyz'
leftarr,rightarr=list(alphabets[0:13]),list(alphabets[14::])
print("left array => ",leftarr,"\nright array => ",rightarr,'\n')
user_inp=input("Enter a Characters : ")
final_ans=""
for char in user_inp:
    if leftarr.count(char):
        index=leftarr.index(char)
        final_ans+=rightarr[index]
    else:
        index=rightarr.index(char)
        final_ans+=leftarr[index]

print("Your Input Result: ",user_inp)
print("Converted Result : ",final_ans)