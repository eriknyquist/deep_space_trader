from deep_space_trader.planet import Planet

def check_for_dupes(parts, index):
    count = {}

    for n in parts[index]:
        if n in count:
            count[n] += 1
        else:
            count[n] = 1

    ret = {}
    for n in count:
        if count[n] > 1:
            ret[n] = count[n]

    return ret

def num_possible_names(parts):
    twoparts = len(parts[0]) * len(parts[2])
    threeparts = len(parts[0]) * len(parts[1]) * len(parts[2])
    return twoparts + threeparts


print('{:,} possible planet names'.format(num_possible_names(Planet.parts)))

parts_lists_with_dupes = 0

for i in range(len(Planet.parts)):
    dupes = check_for_dupes(Planet.parts, i)
    if dupes:
        parts_lists_with_dupes += 1
        for n in dupes:
            print("'%s' appears %d times in parts[%d]" % (n, dupes[n], i))

if parts_lists_with_dupes == 0:
    print("No duplicates in any Planets.parts lists")
