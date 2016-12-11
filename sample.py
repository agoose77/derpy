# Python3Programs.txt
# Refresh webpage for latest version of this file!
# anne.dawson@gmail.com
# Last updated: Tuesday 29th November 2016, 14:28 PT, AD
# Note to AD: update this file then copy to Python3Programs.html

# Please Note: lines starting with a # are comments 
# and are ignored by
# the Python interpreter...

# See:
# http://www.annedawson.net/PythonComments.txt
# for important comments about comments.

# Any of these example programs can be run by
# directly copying the desired program and pasting 
# the code to a Python editor such as IDLE...
# http://www.annedawson.net/Python_Program_Run.htm

# The first Python program (01-01.py) has only
# one executable line: 
# print ("Hello World!")
# and one comment line

# A selection of these example programs are used in courses
# CSCI100, CSCI120, CSCI165 and BUSI237


#################################################
# NOTE: These example programs run on Python 3. #
#################################################



# see http://www.annedawson.net/PythonPrograms.html for examples written for Python 2.x

# All Computer Science courses at Coquitlam College now use Python 3


#################################
# READ THE FOLLOWING PARAGRAPH...

# Be aware that there are some significant differences between Python 3
# and earlier versions. For beginner Python programmers, the main ones
# are that the print statement of Python 2.x is now a print function in Python 3,
# (brackets are required after the word print (see program 01-01 below)
# the raw_input function in Python 2.x is replaced by the input function in Python 3,
# and an integer division such as 2/3 in Python 2.x is now a real division
# in Python 3. 

# For experienced programmers, also check out 
# the range() and string formatting differences outlined here:
# http://inventwithpython.com/appendixa.html

# For experienced programmers, also check out 
# IDLE's debugging tools at:
# http://inventwithpython.com/chapter7.html

##############################################################################################

# NOTE FOR USERS OF THIS FILE - all programs shown in this file have been tested with Python 3

##############################################################################################


# 01-01.py

print("Hello World!")

# 01-02.py

thetext = input("Enter some text ")
print("This is what you entered:")
print(thetext)

# 01-03.py

# Note that \n within quote marks forces a new line to be printed
thetext = input("Enter some text\n")
print("This is what you entered:")
print(thetext)

# 01-04.py

prompt = "Enter a some text "
thetext = input(prompt)
print("This is what you entered:")
print(thetext)

# 02-01.py

total = 0.0
number1 = float(input("Enter the first number: "))
total = total + number1
number2 = float(input("Enter the second number: "))
total = total + number2
number3 = float(input("Enter the third number: "))
total = total + number3
average = total / 3
print("The average is " + str(average))

################################################################
#                                                              #
# 02-02.py                                                     #
# Purpose: to demonstrate storage of a floating point number   #
#                                                              #
# Programmer: Anne Dawson                                      #
# Last updated: Sunday 21st March 2010, 12:45 PT               #
#                                                              #
# See this resource to find out how the input function works:  #
# http://www.annedawson.net/Python3_Input.txt                  #
#                                                              #
# See this resource to find out how important comments are:    #
# http://www.annedawson.net/PythonComments.txt                 #
#                                                              #
################################################################
number1 = float(input("Enter the first number: "))
number2 = float(input("Enter the second number: "))
number3 = float(input("Enter the third number: "))
total = number1 + number2 + number3
average = total / 3
print("The average is: ")
print(average)

# 02-03.py
total = 0.0
count = 0
while count < 3:
    number = float(input("Enter a number: "))
    count = count + 1
    total = total + number
average = total / 3
print("The average is " + str(average))

# 03-01.py
sum = 10

# 03-02.py
sum = 10
print(sum)

# 03-03.py
sum = 10
print(sum)
print(type(sum))

# 03-04.py
print(2 + 4)
print(6 - 4)
print(6 * 3)
print(6 / 3)
print(6 % 3)
print(6 // 3)  # floor division: always truncates fractional remainders
print(-5)
print(3 ** 2)  # three to the power of 2

# 03-05.py
print(2.0 + 4.0)
print(6.0 - 4.0)
print(6.0 * 3.0)
print(6.0 / 3.0)
print(6.0 % 3.0)
print(6.0 // 3.0)  # floor division: always truncates fractional remainders
print(-5.0)
print(3.0 ** 2.0)  # three to the power of 2

# 03-06.py

# mixing data types in expressions
# mixed type expressions are "converted up"
# converted up means to take the data type with the greater storage
# float has greater storage (8 bytes) than a regular int (4 bytes)
print(2 + 4.0)
print(6 - 4.0)
print(6 * 3.0)
print(6 / 3.0)
print(6 % 3.0)
print(6 // 3.0)  # floor division: always truncates fractional remainders
print(-5.0)
print(3 ** 2.0)  # three to the power of 2

# 03-07.py

# these are Boolean expressions which result in a value of
# true or false
# Note that Python stores true as integer 1, and false as integer 0
# but outputs 'true' or 'false' from print statements
print(7 > 10)
print(4 < 16)
print(4 == 4)
print(4 <= 4)
print(4 >= 4)
print(4 != 4)

# 03-08.py

# these are string objects
print("Hello out there")
print('Hello')
print("Where's the spam?")
print('x')

# 03-09.py

# these are string assignments
a = "Hello out there"
print(a)
b = 'Hello'
print(b)
c = "Where's the spam?"
print(c)
d = 'x'
print(d)

# 03-10.py

a = 'Hello out there'
b = "Where's the spam?"
c = a + b
print(c)

# 03-11.py

a = 'Hello out there'
b = "Where's the spam?"
c = a + b
print(c)
# d = c + 10
# you cannot concatenate a string and an integer
# you must convert the integer to a string first:
d = c + str(10)
print(d)

# 03-12.py

a = "10"
b = '99'
c = a + b
print(c)
print(type(c))
c = int(c)
print(c)
print(type(c))

# 03-13.py
# How to round up a floating point number
# to the nearest integer
# Updated: Monday 24th January 2011, 16:24 PT, AD

x = 1.6
print(x)
x = round(x)
print(x)
# compare the above with
x = 1.6
x = int(x)
print(x)

# 03-14.py
# How to round a float number to 2 decimal places,
# and output that number as $ currency
# printed with a comma after the number of thousands

# i.e. print 1234.5678 as $1,234.57

# for a list of Python 3's built-in functions, see the link below:
# http://docs.python.org/py3k/library/functions.html

###########################################################################
# PLEASE NOTE: This program will work correctly for some
#              input values, but has not been modified to work in all cases.
###########################################################################

# Updated: Monday 21st February 2011, 5:56 PT, AD

number = 1234.5678
print(number)
number = round(number, 2)
print(number)
# the above line rounds the number to 2 decimal places

thousands = number / 1000
print(thousands)
thousands = int(thousands)
print(thousands)
remainder = number % 1000
print(remainder)
pretty_output = "$" + str(thousands) + "," + str(remainder)
print(pretty_output)

#  File:       04-01.py
#  Purpose:    Creating a string object
#  Programmer: Anne Dawson
#  Course:     CSCI120A, CSCI165
#  Date:       Monday 27th September 2004, 12:43 PT

number1 = input("Enter first number:\n")
print(number1, type(number1))

#  File:       04-02.py
#  Purpose:    Converting one data type to another
#  Programmer: Anne Dawson
#  Course:     CSCI120A, CSCI165
#  Date:       Monday 27th September 2004, 12:46 PT

number1 = input("Enter first number:\n")
print(number1, type(number1))
number1 = int(number1)
print(number1, type(number1))

#  File:       04-03.py
#  Purpose:    Displaying an object's memory location
#  Programmer: Anne Dawson
#  Course:     CSCI120A, CSCI165
#  Date:       Monday 27th September 2004, 12:48 PT

number1 = input("Enter first number:\n")
print(number1, type(number1), id(number1))
number1 = int(number1)
print(number1, type(number1), id(number1))

#  File:       04-04.py
#  Purpose:    Examples of use of arithmetic operators
#  Programmer: Anne Dawson
#  Course:     CSCI120A, CSCI165
#  Date:       Monday 27th September 2004, 13:09 PT

print(2 + 4)
print(6 - 4)
print(6 * 3)
print(6 / 3)
print(6 % 3)
print(6 // 3)  # floor (integer) division: always truncates fractional remainders
print(-5)
print(3 ** 2)  # three to the power of 2

#  File:       04-05.py
#  Purpose:    Examples of use of arithmetic operators with float values
#  Programmer: Anne Dawson
#  Course:     CSCI120A, CSCI165
#  Date:       Monday 27th September 2004, 13:10 PT

print(2.0 + 4.0)
print(6.0 - 4.0)
print(6.0 * 3.0)
print(6.0 / 3.0)
print(6.0 % 3.0)
print(6.0 // 3.0)  # floor (integer) division: always truncates fractional remainders
print(-5.0)
print(3.0 ** 2.0)  # three to the power of 2

#  File:       04-06.py
#  Purpose:    Examples of use of arithmetic operators
#  Programmer: Anne Dawson
#  Course:     CSCI120A, CSCI165
#  Date:       Monday 27th September 2004, 13:10 PT

# mixing data types in expressions
# mixed type expressions are "converted up"
# converted up means to take the data type with the greater storage
# float has greater storage (8 bytes) than a regular int (4 bytes)

print(2 + 4.0)
print(6 - 4.0)
print(6 * 3.0)
print(6 / 3.0)
print(6 % 3.0)
print(6 // 3.0)  # floor division: always truncates fractional remainders
print(-5.0)
print(3 ** 2.0)  # three to the power of 2

#  File:       04-07.py
#  Purpose:    Examples of use of Boolean expressions
#  Programmer: Anne Dawson
#  Course:     CSCI120A, CSCI165
#  Date:       Monday 27th September 2004, 13:12 PT
#  these are Boolean expressions which result in a value of
#  true or false
#  Note that Python stores true as integer 1, and false as integer 0
#  but outputs 'true' or 'false' from print statements
#  If you input Boolean values, you must input 1 or 0.

print(7 > 10)
print(4 < 16)
print(4 == 4)
print(4 <= 4)
print(4 >= 4)
print(4 != 4)

#  File:       04-08.py
#  Purpose:    Displaying boolean values
#  Programmer: Anne Dawson
#  Course:     CSCI120A, CSCI165
#  Date:       Monday 27th September 2004, 12:54 PT

number = 10
isPositive = (number > 0)
print(isPositive)

#  File:       04-09.py
#  Purpose:    Combining boolean expressions with and
#  Programmer: Anne Dawson
#  Course:     CSCI120A, CSCI165
#  Date:       Monday 27th September 2004, 13:18 PT

age = 25
salary = 55000
print((age > 21) and (salary > 50000))

#  File:       04-10.py
#  Purpose:    The if statement
#  Programmer: Anne Dawson
#  Course:     CSCI120A, CSCI165
#  Date:       Monday 27th September 2004, 13:23 PT

#  The condition of the following if statement
#  follows the word if, and ends with a colon (:)
#  In this example, if x has a value equal to 'spam',
#  then 'Hi spam' will be printed.

x = 'spam'
if x == 'spam':
    print('Hi spam')
else:
    print('not spam')

# Notice the indentation (spacing out) of this code.
# The statement(s) following the if condition (i.e. boolean expression)
# must be indented to the next tab stop. This means you must press
# the Tab button before typing the word print.
# Try removing the tab spaces and see what happens when you attempt to run.








#  File:       04-11.py
#  Purpose:    The if statement with multiple statements
#  Programmer: Anne Dawson
#  Course:     CSCI120A, CSCI165
#  Date:       Monday 27th September 2004, 13:23 PT

#  The condition of the following if statement
#  follows the word if, and ends with a colon (:)
#  In this example, if x has a value equal to 'spam',
#  then 'Hi spam\n' will be printed followed by
#  "Nice weather we're having"
#  followed by 'Have a nice day!'


x = 'spam'
if x == 'spam':
    print('Hi spam\n')
    print("Nice weather we're having")
    print('Have a nice day!')
else:
    print('not spam')

# Notice the indentation (spacing out) of this code.
# The statement(s) following the if condition (i.e. boolean expression)
# must be indented to the next tab stop. This means you must press
# the Tab button before typing the word print.
# Try removing the tab spaces and see what happens when you attempt to run.











#  File:       04-12.py
#  Purpose:    The if statement with multiple statements
#  Programmer: Anne Dawson
#  Course:     CSCI120A, CSCI165
#  Date:       Monday 27th September 2004, 13:23 PT

#  The condition of the following if statement
#  follows the word if, and ends with a colon (:)
#  In this example, if x has a value equal to 'spammy',
#  then 'Hi spam\n' will be printed followed by
#  "Nice weather we're having"
#  followed by 'Have a nice day!'

x = 'spam'
if x == 'spammy':
    print('Hi spam\n')
    print("Nice weather we're having")
    print('Have a nice day!')
else:
    print('not spam')
    print('Not having a good day?')

# Notice the indentation (spacing out) of this code.
# The statement(s) following the if condition (i.e. boolean expression)
# must be indented to the next tab stop. This means you must press
# the Tab button before typing the word print.
# Try removing the tab spaces and see what happens when you attempt to run.











#  Program:    04-13.py
#  Purpose:    A nested if example (an if statement within another if statement)
#  Programmer: Anne Dawson
#  Course:     CSCI120A, CSCI165
#  Date:       Monday 4th October 2004, 13:21 PT

score = input("Enter score: ")
score = int(score)
if score >= 80:
    grade = 'A'
else:
    if score >= 70:
        grade = 'B'
    else:
        grade = 'C'
print("\n\nGrade is: " + grade)

#  Program:    04-14.py
#  Purpose:    A nested if example - using if/else
#  Programmer: Anne Dawson
#  Course:     CSCI120A, CSCI165
#  Date:       Monday 4th October 2004, 13:25 PT

score = input("Enter score: ")
score = int(score)
if score >= 80:
    grade = 'A'
else:
    if score >= 70:
        grade = 'B'
    else:
        if score >= 55:
            grade = 'C'
        else:
            if score >= 50:
                grade = 'Pass'
            else:
                grade = 'Fail'
print("\n\nGrade is: " + grade)

#  Program:    04-15A.py
#  Purpose:    A nested if example - using if/elif/else
#  Programmer: Anne Dawson
#  Course:     CSCI120A, CSCI165
#  Date:       Monday 21st September 2015, 6:48 PT

score = input("Enter score: ")
score = int(score)
if score > 80 or score == 80:
    grade = 'A'
elif score > 70 or score == 70:
    grade = 'B'
elif score > 55 or score == 55:
    grade = 'C'
elif score > 50 or score == 50:
    grade = 'Pass'
else:
    grade = 'Fail'
print("\n\nGrade is: " + grade)

#  Program:    04-15B.py
#  Purpose:    A nested if example - using if/elif/else
#  Programmer: Anne Dawson
#  Course:     CSCI120A, CSCI165
#  Date:       Monday 4th October 2004, 13:28 PT

score = input("Enter score: ")
score = int(score)
if score >= 80:
    grade = 'A'
elif score >= 70:
    grade = 'B'
elif score >= 55:
    grade = 'C'
elif score >= 50:
    grade = 'Pass'
else:
    grade = 'Fail'
print("\n\nGrade is: " + grade)

#  File:       04-16.py
#  Purpose:    Demo of DeMorgan's Laws:
#  1.  a Not And is equivalent to an Or with two negated inputs
#  2.  a Not Or is equivalent to an And with two negated inputs
#  Programmer: Anne Dawson
#  Course:     CSCI120A, CSCI165
#  Date:       Monday 21st March 2005, 05:53 PT
#  Test data: 0 0, 0 1, 1 0, 1 1
#  For ***any*** value of x and y, (not(x < 15 and y >= 3)) == (x >= 15 or y < 3)
#  Common uses of De Morgan's rules are in digital circuit design
#  where it is used to manipulate the types of logic gates.
#  Also, computer programmers use them to change a complicated statement
#  like IF ... AND (... OR ...) THEN ... into its opposite (and shorter) equivalent.
#  http://en.wikipedia.org/wiki/De_Morgan%27s_law
#  http://www.coquitlamcollege.com/adawson/DeMorgansLaws.htm

x = int(input("Enter a value for x: "))
y = int(input("Enter a value for y: "))
print((not (x < 15 and y >= 3)))
print((x >= 15 or y < 3))

#  Program:    04-17.py
#  Purpose:    Decision using two conditions linked with an and or an or
#  Programmer: Anne Dawson
#  Course:     CSCI120A, CSCI165
#  Date:       Tuesday 20th February 2007, 11:20 PT

age = input("Enter your age: ")
age = int(age)
have_own_car = input("Do you own your own car (y/n): ")

if (age > 21) and (have_own_car == 'y'):
    print("You are over 21 years old and own your own car")

if (age > 21) and (have_own_car == 'n'):
    print("You are over 21 years old and you do NOT own your own car")

if (age == 21) and (have_own_car == 'y'):
    print("You are 21 years old and you own your own car")

if (age == 21) and (have_own_car == 'n'):
    print("You are 21 years old and you DO NOT own your own car")

if (age < 21) and (have_own_car == 'y'):
    print("You are younger than 21 and you own your own car")

if (age < 21) and (have_own_car == 'n'):
    print("You are younger than 21 and you DO NOT own your own car")

salary = float(input("Enter your annual salary, (e.g. 50000): "))

if (salary > 50000) or (age > 21):
    print("you can join our club because you earn more than $50000 OR you are over 21 (or both)")
else:
    print("you need to be earning more than 50000 OR be over 21 (or both) to join our club")

# File:       05-01.py
#  Purpose:    Examples of while loops
#  Programmer: Anne Dawson
#  Course:     CSCI120A, CSCI165
#  Date:       Thursday 30th September 2004, 15:51 PT

#  You must remember to indent the statements to be repeated.
#  They must be repeated to the same level.
#  Use the Tab key to indent. The space bar can be used but
#  its easier (less typing) to use the space bar

#  Used like this, the while loop is said to be
#  'counter-controlled'. In this program, x is acting as a counter.

x = 1
while x < 5:
    print('Hi spam')
    x = x + 1
print('done')

#  File:       05-02.py
#  Purpose:    Examples of while loops
#  Programmer: Anne Dawson
#  Course:     CSCI120A, CSCI165
#  Date:       Thursday 30th September 2004, 15:51 PT

#  Used like this, the while loop is said to be
#  'counter-controlled'. In this program, x is acting as a counter.

#  You may repeat one statement or multiple statements.

x = 1
while x < 5:
    print('Hi spam')
    x = x + 1
    print('I love spam')
print('done')
print('gone')

#  File:       05-03.py
#  Purpose:    Examples of while loops - the infinite loop
#  Programmer: Anne Dawson
#  Course:     CSCI120A, CSCI165
#  Date:       Thursday 30th September 2004, 15:51 PT

#  An infinite loop.
#  Remember that 1 (or any value other than 0) represents true.
#  Press Ctrl-C to interrupt this program run.

x = 1
while x:
    print('Hi spam')
    x = x + 1
    print('I love spam')
    print('Press the Ctrl key and the C key together')
    print('to interrupt this program...')
print('done')
print('gone')

#  File:       05-04.py
#  Purpose:    Examples of while loops - another infinite loop
#  Programmer: Anne Dawson
#  Course:     CSCI120A, CSCI165
#  Date:       Thursday 30th September 2004, 16:00 PT

#  An infinite loop.
#  Remember that 1 (or any value other than 0) represents true.
#  Press Ctrl-C to interrupt this program run.


while 1:
    print('Anyone for spam? ')
    print('Press the Ctrl key and the C key together')
    print('to interrupt this program...')
print('done')
print('gone')

#  File:       05-05.py
#  Purpose:    Example: use of break to end an infinite loop
#  Programmer: Anne Dawson
#  Course:     CSCI120A, CSCI165
#  Date:       Thursday 30th September 2004, 16:02 PT


while 1:
    print('Spam')
    answer = input('Press y to end this loop')
    if answer == 'y':
        print('Fries with that?')
        break
print('Have a ')
print('nice day!')

#  File:       05-06.py
#  Purpose:    Example: use of continue in a loop
#  Programmer: Anne Dawson
#  Course:     CSCI120A, CSCI165
#  Date:       Thursday 30th September 2004, 16:07 PT


while 1:
    print('Spam')
    answer = input('Press y for large fries ')
    if answer == 'y':
        print('Large fries with spam, mmmm, yummy ')
        continue
    answer = input('Had enough yet? ')
    if answer == 'y':
        break
print('Have a ')
print('nice day!')
