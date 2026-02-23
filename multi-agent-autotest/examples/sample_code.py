def fizzbuzz(n: int) -> list[str]:
    """Retorna lista com FizzBuzz de 1 até n."""
    result = []
    for i in range(1, n + 1):
        if i % 15 == 0:
            result.append("FizzBuzz")
        elif i % 3 == 0:
            result.append("Fizz")
        elif i % 5 == 0:
            result.append("Buzz")
        else:
            result.append(str(i))
    return result


def two_sum(nums: list[int], target: int) -> list[int]:
    """Retorna índices dos dois números que somam ao target."""
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []


def is_palindrome(s: str) -> bool:
    """Verifica se uma string é palíndromo (ignora maiúsculas e espaços)."""
    cleaned = "".join(c.lower() for c in s if c.isalnum())
    return cleaned == cleaned[::-1]


def max_subarray(nums: list[int]) -> int:
    """Kadane's algorithm — retorna a soma máxima de subarray contíguo."""
    if not nums:
        raise ValueError("Lista não pode ser vazia")
    max_sum = current = nums[0]
    for num in nums[1:]:
        current = max(num, current + num)
        max_sum = max(max_sum, current)
    return max_sum


def climbing_stairs(n: int) -> int:
    """Quantas formas distintas de subir n degraus (1 ou 2 por vez)."""
    if n <= 0:
        raise ValueError("n deve ser positivo")
    if n == 1:
        return 1
    a, b = 1, 2
    for _ in range(2, n):
        a, b = b, a + b
    return b


def valid_parentheses(s: str) -> bool:
    """Verifica se os parênteses, colchetes e chaves estão balanceados."""
    stack = []
    mapping = {")": "(", "]": "[", "}": "{"}
    for char in s:
        if char in mapping:
            top = stack.pop() if stack else "#"
            if mapping[char] != top:
                return False
        else:
            stack.append(char)
    return not stack
