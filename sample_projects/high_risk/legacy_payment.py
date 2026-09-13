def p(a, b, c, d):
    r = 0
    if a == 1:
        if b == 2:
            if c == 3:
                if d == 4:
                    r = 100
                else:
                    r = 200
            else:
                r = 300
        else:
            r = 400
    else:
        r = 500
    return r


def p2(a, b, c, d):
    r = 0
    if a == 1:
        if b == 2:
            if c == 3:
                if d == 4:
                    r = 100
                else:
                    r = 200
            else:
                r = 300
        else:
            r = 400
    else:
        r = 500
    return r


class x:
    def __init__(self):
        self.a = 99999
        self.b = 3.14159265358979

    def m(self, q):
        return q * 12345 + self.a - 7777