"""Linked list, binary search tree, and deque implemented from scratch."""

import random as _rnd

# ── Doubly-linked list ────────────────────────────────────────────────────────


class Node:
    def __init__(self, value):
        self.value = value
        self.prev = None
        self.next = None


class DoublyLinkedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0

    def append(self, value):
        node = Node(value)
        if self.tail is None:
            self.head = self.tail = node
        else:
            node.prev = self.tail
            self.tail.next = node
            self.tail = node
        self.size += 1

    def prepend(self, value):
        node = Node(value)
        if self.head is None:
            self.head = self.tail = node
        else:
            node.next = self.head
            self.head.prev = node
            self.head = node
        self.size += 1

    def remove(self, value):
        cur = self.head
        while cur:
            if cur.value == value:
                if cur.prev:
                    cur.prev.next = cur.next
                else:
                    self.head = cur.next
                if cur.next:
                    cur.next.prev = cur.prev
                else:
                    self.tail = cur.prev
                self.size -= 1
                return True
            cur = cur.next
        return False

    def to_list(self):
        result = []
        cur = self.head
        while cur:
            result.append(cur.value)
            cur = cur.next
        return result

    def reverse(self):
        cur = self.head
        while cur:
            cur.prev, cur.next = cur.next, cur.prev
            cur = cur.prev
        self.head, self.tail = self.tail, self.head


# ── Binary search tree ────────────────────────────────────────────────────────


class BSTNode:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None
        self.height = 1


class BST:
    def __init__(self):
        self.root = None

    def insert(self, key):
        self.root = self._insert(self.root, key)

    def _insert(self, node, key):
        if node is None:
            return BSTNode(key)
        if key < node.key:
            node.left = self._insert(node.left, key)
        elif key > node.key:
            node.right = self._insert(node.right, key)
        return node

    def search(self, key):
        node = self.root
        while node:
            if key == node.key:
                return True
            node = node.left if key < node.key else node.right
        return False

    def inorder(self):
        result = []
        stack = []
        cur = self.root
        while cur or stack:
            while cur:
                stack.append(cur)
                cur = cur.left
            cur = stack.pop()
            result.append(cur.key)
            cur = cur.right
        return result

    def height(self):
        def _h(node):
            if node is None:
                return 0
            return 1 + max(_h(node.left), _h(node.right))

        return _h(self.root)

    def min_value(self):
        node = self.root
        while node and node.left:
            node = node.left
        return node.key if node else None

    def max_value(self):
        node = self.root
        while node and node.right:
            node = node.right
        return node.key if node else None


# ── Circular deque ────────────────────────────────────────────────────────────


class Deque:
    def __init__(self, capacity=16):
        self._buf = [None] * capacity
        self._head = 0
        self._size = 0

    def _grow(self):
        cap = len(self._buf)
        new_buf = [None] * (cap * 2)
        for i in range(self._size):
            new_buf[i] = self._buf[(self._head + i) % cap]
        self._buf = new_buf
        self._head = 0

    def push_back(self, item):
        if self._size == len(self._buf):
            self._grow()
        tail = (self._head + self._size) % len(self._buf)
        self._buf[tail] = item
        self._size += 1

    def push_front(self, item):
        if self._size == len(self._buf):
            self._grow()
        self._head = (self._head - 1) % len(self._buf)
        self._buf[self._head] = item
        self._size += 1

    def pop_back(self):
        if self._size == 0:
            raise IndexError("deque is empty")
        tail = (self._head + self._size - 1) % len(self._buf)
        val = self._buf[tail]
        self._size -= 1
        return val

    def pop_front(self):
        if self._size == 0:
            raise IndexError("deque is empty")
        val = self._buf[self._head]
        self._head = (self._head + 1) % len(self._buf)
        self._size -= 1
        return val

    def __len__(self):
        return self._size

    def to_list(self):
        return [self._buf[(self._head + i) % len(self._buf)] for i in range(self._size)]


# ── Exercises ─────────────────────────────────────────────────────────────────

dll = DoublyLinkedList()
for v in [10, 20, 30, 40, 50]:
    dll.append(v)
dll.prepend(5)
dll.remove(30)
print("dll forward:", dll.to_list())
dll.reverse()
print("dll reversed:", dll.to_list())
print("dll size:", dll.size)

bst = BST()
keys = [50, 30, 70, 20, 40, 60, 80, 10, 25, 35, 45]
for k in keys:
    bst.insert(k)
print("bst inorder:", bst.inorder())
print("bst height:", bst.height())
print("bst min:", bst.min_value(), "max:", bst.max_value())
for k in [25, 55, 80, 1]:
    print(f"  search({k}): {bst.search(k)}")

dq = Deque(4)
for v in range(1, 9):
    dq.push_back(v)
for v in [0, -1]:
    dq.push_front(v)
print("deque:", dq.to_list())
print("pop_back:", dq.pop_back())
print("pop_front:", dq.pop_front())
print("deque after pops:", dq.to_list())

# stress: sort using BST (tree sort)
_rnd.seed(42)
random_vals = [_rnd.randint(0, 1000) for _ in range(50)]
tree = BST()
for v in random_vals:
    tree.insert(v)
tree_sorted = tree.inorder()
direct_sorted = sorted(set(random_vals))
print("tree-sort matches sorted(set):", tree_sorted == direct_sorted)
print("tree-sort length:", len(tree_sorted))
