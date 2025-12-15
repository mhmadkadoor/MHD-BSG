import datetime
kegenvalue = datetime.datetime.now().microsecond
print(f"Key generation value: {kegenvalue}")
def generate_key(value):
    value = int(value-5)
    key = 0
    while value > 1:
        key <<= 1
        if value & 1:
            # print(f"odd value: {value}")
            value = int((value * 3) + 1)
        else:
            key |= 1
            # print(f"even value: {value}")
            value = int(value / 2)
    return key

generated_key = generate_key(kegenvalue)
print(bin(generated_key))