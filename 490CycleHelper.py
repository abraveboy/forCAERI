#   Date:2021.1.5
# Author:Jiangxin
#    Des:优化490台架循环9工况问题

def read_text(fpath='test.txt'):
    source_data = []
    with open(fpath) as fp:
        source = fp.readlines()
        source = source[17:]
        source = source[:-21]
        return source


class Cycle:
    def __init__(self, pnts):
        self.points = []

        self.__loc_nrate = 0
        for pt_str in pnts:
            pt = []
            pt_str = pt_str.replace("\n", "")
            pt_str = pt_str.replace(",", "")
            for i in pt_str.split("   "):
                pt.append(float(i))
            self.points.append(pt)

        self.powers = []
        self.torques = []
        self.speeds = []
        for pt in self.points:
            self.powers.append(pt[3])
            self.torques.append(pt[2])
            self.speeds.append(pt[1])

        self.max_power = max(self.powers)
        for j in range(len(self.powers)):
            if self.powers[j] == self.max_power:
                self.__loc_nrate = j
                break
        self.nlo = self.get_lo()
        self.nhi = self.get_nhi()
        self.n95 = self.get_n95()
        self.nidle = self.get_nidle()
        self.npref = self.get_npref()
        self.react_speed = self.get_react_speed()
        self.etc_nref = self.get_whtc2etc_ref()
        self.react_torque = self.get_react_torque()

    def __search_right(self, target, target_group, start=0):
        lower = higher = self.max_power
        loc = 0
        for i in range(start, len(target_group)):
            loc = i
            if target_group[i] >= target:
                higher = target_group[i]
            if target_group[i] < target:
                lower = target_group[i]
                break
        if higher - target < target - lower:
            return loc - 1
        else:
            return loc

    def __search_left(self, target, target_group):
        lower = higher = 0
        loc = 0
        for i in range(len(target_group)):
            loc = i
            if target_group[i] <= target:
                lower = target_group[i]
            if target_group[i] > target:
                higher = target_group[i]
                break
        if higher - target > target - lower:
            return loc - 1
        else:
            return loc

    def get_location_by_power(self, per, flag=0):
        # 最大净功率55%所对应的最低发动机转速
        pnt_power = self.max_power * per
        if flag == 0:
            index = self.__search_left(pnt_power, self.powers)
            return index
        if flag == 1:
            index = self.__search_right(pnt_power, self.powers, start=self.__loc_nrate)
            return index

    def get_lo(self, per=0.55):
        # 最大净功率55%所对应的最低发动机转速
        loc_lo = self.get_location_by_power(per)
        return self.speeds[loc_lo]

    def get_npref(self):
        # 从怠速到n95对相应转速下的扭矩最大值进行积分，整个积分值得51%所对应的发动机转速
        start = 0
        end = self.get_location_by_power(0.95, flag=1)
        total_torque = 0
        part_torque = 0
        for i in range(start, end):
            total_torque += self.torques[i] * 8

        next_torque = 0
        demond_torque = 0.51 * total_torque
        for i in range(start, end):
            next_torque += self.torques[i] * 8
            if next_torque > demond_torque:
                if next_torque - demond_torque < demond_torque - part_torque:
                    return self.speeds[i]
                return self.speeds[i - 1]
            part_torque = next_torque

    def get_nhi(self, per=0.70):
        # 最大净功率70%所对应的最高发动机转速
        loc_hi = self.get_location_by_power(per, flag=1)
        return self.speeds[loc_hi]

    def get_nidle(self):
        # 发动机怠速
        return int(self.speeds[0])

    def get_n95(self, per=0.95):
        # 最大净功率95%所对应的最高发动机转速
        loc_n95 = self.get_location_by_power(per, flag=1)
        return self.speeds[loc_n95]

    def get_react_speed(self, nnorm=0.55):
        self.react_speed = nnorm * (
                0.45 * self.nlo + 0.45 * self.npref + 0.1 * self.nhi - self.nidle) * 2.0327 + self.nidle
        return self.react_speed

    def get_whtc2etc_ref(self):
        # 490台架特性，需要将参考转速修改为国五的
        self.etc_nref = (0.45 * self.nlo + 0.45 * self.npref + 0.1 * self.nhi - self.nidle) * 2.0327 + self.nidle
        return self.etc_nref

    def get_react_torque(self, mnorm=0.5):
        self.react_torque = mnorm * max(self.torques)
        return self.react_torque


if __name__ == '__main__':
    cycle = Cycle(read_text("full_load_curve.txt"))

    print(" _______                  ______            _       ")
    print("(_______)                / _____)          | |      ")
    print(" _____   ____  ___ _   _| /     _   _  ____| | ____ ")
    print("|  ___) / _  |/___) | | | |    | | | |/ ___) |/ _  )")
    print("| |____( ( | |___ | |_| | \____| |_| ( (___| ( (/ / ")
    print("|_______)_||_(___/ \__  |\______)__  |\____)_|\____)")
    print("                  (____/       (____/               ")

    print("")
    print("动态外特性详情")
    print("{:>20}:   {:4.0f} r/min".format("idle", cycle.nidle))
    print("{:>20}:   {:4.0f} r/min".format("nlo", cycle.nlo))
    print("{:>20}:   {:4.0f} r/min".format("nhi", cycle.nhi))
    print("{:>20}:   {:4.0f} r/min".format("n95", cycle.n95))
    print("{:>20}:   {:4.0f} r/min".format("whtc_npref", cycle.npref))
    print("{:>20}:   {:4.0f} r/min".format("etc_ref", cycle.etc_nref))
    print("{:>20}:   {:4.0f} r/min".format("9th Speed", cycle.get_react_speed(0.55)))
    print("{:>20}:   {:4.0f} N".format("9th Torque", cycle.get_react_torque(0.50)))
    input('任意键退出')





