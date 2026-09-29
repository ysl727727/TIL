done = False
if done:
    print("수고했어요")
else:
    print("시작해 볼까요")

priority = 3
if priority == 1:
    print("먼저 처리")
elif priority == 2:
    print("오늘 처리")
else:
    print("시간 날 때")

birth_date = input("태어난 년도를 입력하세요")
gender = input("성별을 입력하세요")

if int(birth_date) < 2000:
    if gender == "남성":
        print("start with 1")
    elif gender == "여성":
        print("start with 2")
    else:
        print("성별이 올바르지 않습니다.")

if int(birth_date) >= 2000:
    if gender == "남성":
        print("start with 3")
    elif gender == "여성":
        print("start with 4")
    else:
        print("성별이 올바르지 않습니다.")

member = ["karina"]
extra_member = ["winter", "ningning"]
# final_member == ["karina","winter","ninggning","Giselle"] 을 만들어라.

member.extend(extra_member)
member.append("Giselle")
print(member)

numbers = [3,6,32,15,4,1]

#숫자 32를 지우시오
#그 후 2번째 element를 지우시오
#그 후 반대로 정렬하시오
#결과를 print 하시오

numbers.remove(32)
numbers.pop(2)
numbers.sort(reverse=True)
print(numbers)