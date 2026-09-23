


def Solution:
    x1 = "alice, 50, sf"
    ex2 = "bob, 30, ny"

    list = [ex1, ex2]

    reference = {}

    for item in list:
        name, minute, city = item.split(",")
        

        if name not in reference:
            reference[name] = {
                "city": city
                "minute": minute
            }
        else:
            if city != reference[name]["city"]:
                if minute <= reference[name]["minute"] + 60:
                    print("False")
                    return False

    print("True")
    return True

Solution()
        

        




    

    