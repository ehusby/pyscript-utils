
def mean(nums):
    cnt = len(nums)
    if cnt == 0:
        return None
    return sum(nums) / float(cnt)

def median(nums):
    cnt = len(nums)
    if cnt == 0:
        return None
    nums = sorted(nums)
    med_idx = cnt // 2
    if cnt % 2 == 1:
        return nums[med_idx]
    else:
        return sum(nums[(med_idx-1):(med_idx+1)]) / float(2)
