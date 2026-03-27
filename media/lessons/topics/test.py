a = input()
b = input()
if (a == 'blue' and b == 'red') or (b == 'blue' and a == 'red'):
    print('purple')
elif (a == 'blue' and b == 'green') or (b == 'blue' and c == 'green'):
    print('cyan')
elif (a == 'red' and b =='green') or (b == 'red' and c =='green'):
    print('yellow')
else:
    print('error')
