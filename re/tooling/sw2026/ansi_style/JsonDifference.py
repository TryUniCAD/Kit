def difference(left, right, path=""):
    if isinstance(left, dict) and isinstance(right, dict):
        result = []
        for key in sorted(set(left) | set(right)):
            if key not in left or key not in right:
                result.append(
                    {
                        "path": path + "/" + key,
                        "left_present": key in left,
                        "right_present": key in right,
                        "left": left.get(key),
                        "right": right.get(key),
                    }
                )
            else:
                result.extend(difference(left[key], right[key], path + "/" + key))
        return result
    if isinstance(left, list) and isinstance(right, list):
        result = []
        for index in range(max(len(left), len(right))):
            if index >= min(len(left), len(right)):
                result.append(
                    {
                        "path": path + "/" + str(index),
                        "left_present": index < len(left),
                        "right_present": index < len(right),
                        "left": left[index] if index < len(left) else None,
                        "right": right[index] if index < len(right) else None,
                    }
                )
            else:
                result.extend(
                    difference(left[index], right[index], path + "/" + str(index))
                )
        return result
    return [] if left == right else [{"path": path, "left": left, "right": right}]
