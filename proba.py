from dataclasses import dataclass
import random

@dataclass(eq=True,frozen=True)
class Whale:

    name: str
    support: bool
    ilvl: int

    def __gt__(self, other):
        if isinstance(other, Whale):
            return self.ilvl > other.ilvl

    def __lt__(self, other):
        if isinstance(other, Whale):
            return self.ilvl < other.ilvl

    def __ne__(self, other):
        if isinstance(other, Whale):
            return self.ilvl != other.ilvl

    def __ge__(self, other):
        if isinstance(other, Whale):
            return self.ilvl >= other.ilvl

    def __le__(self, other):
        if isinstance(other, Whale):
            return self.ilvl <= other.ilvl

    def __str__(self):
        return f"{self.name} - {self.ilvl} - {'Support' if self.support else 'DPS'}"

if __name__ == "__main__":
    WhaleList = []


    WhaleList.append(Whale("Pedrada", False, 1434))
    WhaleList.append(Whale("Nivlek", False, 1436))
    WhaleList.append(Whale("Skurzasty", False, 1447))
    WhaleList.append(Whale("Dfault", False, 1412))
    WhaleList.append(Whale("Itzkira", False, 1423))
    WhaleList.append(Whale("Kuroishii", False, 1440))
    WhaleList.append(Whale("Civ", True, 1435))
    WhaleList.append(Whale("Witchslayer", True, 1425))
    WhaleList.append(Whale("HappyWhale", False, 1431))
    WhaleList.append(Whale("SFM", False, 1428))


    #WhaleList.append(Whale("Bluegunlancer", False, 1403))
    #WhaleList.append(Whale("Keinaa", True, 1445))
    #WhaleList.append(Whale("Akane", False, 1400))





    # P2


    for i in WhaleList:
        print(i)

    WhaleList.sort()

    print(f"The numbers of people are: {len(WhaleList)}")

    support_list = [s for s in WhaleList if s.support]
    dps_list = [d for d in WhaleList if not d.support]

    # probably unnecessary
    support_list.sort()
    dps_list.sort()

    max_number_of_groups = len(WhaleList) // 4 if len(WhaleList) % 4 == 0 else (len(WhaleList) // 4) + 1
    print(f"Max number of groups: {max_number_of_groups}\n\n")
    group_dict = {}
    # make 3 man groups first  1 dps from top, 1 from bottom 1 random support
    for i in range(max_number_of_groups):
        if dps_list:
            group_set = {dps_list[0], dps_list[len(dps_list) - 1]}
            del dps_list[0]
            if len(group_set) == 2:
                del dps_list[len(dps_list) - 1]
            if support_list:
                random_support = random.choice(support_list)
                support_list.remove(random_support)
                group_set.add(random_support)
        else:
            group_set = set()

        group_dict[i] = group_set


    finalized_groups = {}

    # distribute the remaining members
    while dps_list or support_list:
        most_filled_groups_number = max([len(group_dict[d]) for d, v in group_dict.items()])

        random_group = random.choice(list(group_dict))
        while len(group_dict[random_group]) != most_filled_groups_number:
            random_group = random.choice(list(group_dict))

        random_number = random.randint(0, 2)
        if random_number == 0:
            if dps_list:
                random_member = random.choice(dps_list)
                dps_list.remove(random_member)
            elif support_list:
                random_member = random.choice(support_list)
                support_list.remove(random_member)
        else:
            if support_list:
                random_member = random.choice(support_list)
                support_list.remove(random_member)
            elif dps_list:
                random_member = random.choice(dps_list)
                dps_list.remove(random_member)

        random_group_set = group_dict.pop(random_group)
        random_group_set.add(random_member)
        if len(random_group_set) != 4:
            group_dict[random_group] = random_group_set
        else:
            finalized_groups[random_group] = random_group_set

    for idx, group in enumerate(finalized_groups):
        print(f"The {idx + 1}. group are:")
        for whale in finalized_groups[group]:
            print(f"\t{whale}")
        print()
    print("----------------------------------------------")
    for idx, group in enumerate(group_dict):
        print(f"The {(idx + 1) + len(finalized_groups)}. group are:")
        for whale in group_dict[group]:
            print(f"\t{whale}")
        print()












