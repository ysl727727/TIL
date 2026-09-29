phones = {"Apple": "iphone"}
#"Samsung" : "Galaxy" 추가
# 제조사들을 출력하시오
#Samsung > Samsung Electronics로 바꾸시오.

phones.update({"Samsung":"Galaxy"})
print(phones)
print(phones.keys())
phones.update({"Samsung":"Galaxy Series"})
print(phones)

#for문을 이용하시오

matrix = [["apple", "pear", "grape",],["Hyundai", "BMW", "Benz"]]
#Hyundai의 index 값을 출력하시오
for i in range(len(matrix)):
    for j in range(len(matrix[1])):
        if matrix[i][j] == "Hyundai":
            print(i,j)

matrix = [["apple" ,"pear", "grape",],["Hyundai", "BMW", "Benz"]]
#apple의 index값을 구하면?

for i in range(len(matrix)):
    for j in range(len(matrix[0])):
        if matrix[i][j] == "apple":
            print(i,j)

# BMW는?

for i in range(len(matrix)):
    for j in range(len(matrix[1])):
        if matrix[i][j] == "BMW":
            print(i,j)



#모든 짝수의 합을 구하시오. for문 사용
matrix2 = [[2, 3, 5, 4], [9, 11, 12, 15]]
total = 0
for r in matrix2:
    for n in r:
        if n % 2 == 0:
            total += n
print(total)

#홀수의 합을 구하시오
total = 0
for r in matrix2:
    for n in r:
        if n % 2 == 1:
            total += n
print(total)