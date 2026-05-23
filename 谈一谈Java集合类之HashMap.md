---
title: Java集合类之HashMap
date: 2019-07-09 20:44:30
updated: 2019-07-09 20:44:30
tags: HashMap
categories: Java
---

### OverView



### `HashMap`

#### 工作原理



#### 1. jdk 1.7

数据结构：

![](https://s2.ax1x.com/2019/09/09/nJAmNQ.jpg)

看一下Entry的结构：

```java
final K key;
V value;
Entry<K,V> next;
int hash;
```

put方法：

```java
public V put(K key, V value) {
        if (table == EMPTY_TABLE) {
            inflateTable(threshold);
        }
        if (key == null)
            return putForNullKey(value);
        int hash = hash(key);
        int i = indexFor(hash, table.length);
        for (Entry<K,V> e = table[i]; e != null; e = e.next) {
            Object k;
            if (e.hash == hash && ((k = e.key) == key || key.equals(k))) {
                V oldValue = e.value;
                e.value = value;
                e.recordAccess(this);
                return oldValue;
            }
        }

        modCount++;
        addEntry(hash, key, value, i);
        return null;
    }
```

```java
void addEntry(int hash, K key, V value, int bucketIndex) {
        if ((size >= threshold) && (null != table[bucketIndex])) {
            resize(2 * table.length);
            hash = (null != key) ? hash(key) : 0;
            bucketIndex = indexFor(hash, table.length);
        }

        createEntry(hash, key, value, bucketIndex);
    }
```

```java
void createEntry(int hash, K key, V value, int bucketIndex) {
        Entry<K,V> e = table[bucketIndex];
        table[bucketIndex] = new Entry<>(hash, key, value, e);
        size++;
    }
```



resize方法：

```java
void resize(int newCapacity) {
        Entry[] oldTable = table;
        int oldCapacity = oldTable.length;
        if (oldCapacity == MAXIMUM_CAPACITY) {
            threshold = Integer.MAX_VALUE;
            return;
        }

        Entry[] newTable = new Entry[newCapacity];
        transfer(newTable, initHashSeedAsNeeded(newCapacity));
        table = newTable;
        threshold = (int)Math.min(newCapacity * loadFactor, MAXIMUM_CAPACITY + 1);
    }
```

```java
void transfer(Entry[] newTable, boolean rehash) {
        int newCapacity = newTable.length;
        for (Entry<K,V> e : table) {
            while(null != e) {
                Entry<K,V> next = e.next;
                if (rehash) {
                    e.hash = null == e.key ? 0 : hash(e.key);
                }
                int i = indexFor(e.hash, newCapacity);
                e.next = newTable[i];
                newTable[i] = e;
                e = next;
            }
        }
    }
```



#### 2. jdk 1.8

在1.7的实现中，每个桶中的链表过长后会造成查询时间增长，针对此，在1.8中进行了优化，当链表超过一定长度时，使用红黑树来代替。

数据结构：

![](https://s2.ax1x.com/2019/09/09/nJZDuq.jpg)

相比1.7中的成员变量，主要有以下改动:

+ 增加了`TREEIFY_THRESHOLD`和`UNTREEIFY_THRESHOLD`:将链表转为红黑树的阈值,以及在resize时将红黑树转为链表的阈值。
+ 将`Entry`改为`Node`

Node的数据结构如下：

```java
final int hash;
final K key;
V value;
Node<K,V> next;
```

put方法：

```java
final V putVal(int hash, K key, V value, boolean onlyIfAbsent,
                   boolean evict) {
        Node<K,V>[] tab; Node<K,V> p; int n, i;
        //如果表空
        if ((tab = table) == null || (n = tab.length) == 0)
            n = (tab = resize()).length;
        //如果当前桶空
        if ((p = tab[i = (n - 1) & hash]) == null)
            tab[i] = newNode(hash, key, value, null);
        else {
            Node<K,V> e; K k;
            //如果有key相同的元素
            if (p.hash == hash &&
                ((k = p.key) == key || (key != null && key.equals(k))))
                e = p;
            //如果是tree节点
            else if (p instanceof TreeNode)
                e = ((TreeNode<K,V>)p).putTreeVal(this, tab, hash, key, value);
            //如果是链表节点
            else {
                for (int binCount = 0; ; ++binCount) {
                    if ((e = p.next) == null) {
                        p.next = newNode(hash, key, value, null);
                        if (binCount >= TREEIFY_THRESHOLD - 1) // -1 for 1st
                            treeifyBin(tab, hash);
                        break;
                    }
                    if (e.hash == hash &&
                        ((k = e.key) == key || (key != null && key.equals(k))))
                        break;
                    p = e;
                }
            }
            if (e != null) { // existing mapping for key
                V oldValue = e.value;
                if (!onlyIfAbsent || oldValue == null)
                    e.value = value;
                afterNodeAccess(e);
                return oldValue;
            }
        }
        //检查容量是否到达阈值
        ++modCount;
        if (++size > threshold)
            resize();
        afterNodeInsertion(evict);
        return null;
    }
```

get方法：

```java
final Node<K,V> getNode(int hash, Object key) {
        Node<K,V>[] tab; Node<K,V> first, e; int n; K k;
        if ((tab = table) != null && (n = tab.length) > 0 &&
            (first = tab[(n - 1) & hash]) != null) {
            if (first.hash == hash && // always check first node
                ((k = first.key) == key || (key != null && key.equals(k))))
                return first;
            if ((e = first.next) != null) {
                if (first instanceof TreeNode)
                    return ((TreeNode<K,V>)first).getTreeNode(hash, key);
                do {
                    if (e.hash == hash &&
                        ((k = e.key) == key || (key != null && key.equals(k))))
                        return e;
                } while ((e = e.next) != null);
            }
        }
        return null;
    }
```



需要注意的是，`HashMap`和其他集合类一样，也有扩容的操作，当entries的数量超过容量阈值时，会自动扩容。所谓扩容，就是把里面的元素移植到一个更大的`HashMap`中，里面所有的元素都要进行以此重新hash.

即使1.8中进行了优化，但是hashmap还是存在一些不可避免的问题，比如：线程不安全。当在扩容的过程中有多个线程一起操作时，很有可能会造成链表首位相连，形成死循环。Javadoc中有这么一句话

```
<p><strong>Note that this implementation is not synchronized.</strong>
If multiple threads access a hash map concurrently, and at least one of
the threads modifies the map structurally, it <i>must</i> be
synchronized externally.  (A structural modification is any operation
that adds or deletes one or more mappings; merely changing the value
associated with a key that an instance already contains is not a
structural modification.)  This is typically accomplished by
synchronizing on some object that naturally encapsulates the map.
```

就是说在对HashMap做结构性修改的时候，比如put，remove，resize这种操作，不是线程安全的。其实直观想一想也是，多个线程直接访问这些内容，肯定会有问题的。下面我主要从三个方面来说明它的线程不安全性。

1. 执行put操作的时候

以jdk 1.7为例，在put的代码中有以下方法：

```java
void createEntry(int hash, K key, V value, int bucketIndex) {
        //先保存这个位置本来的元素
        Entry<K,V> e = table[bucketIndex];
        //将新来的元素头插
        table[bucketIndex] = new Entry<>(hash, key, value, e);
        size++;
    }
```

这是一个简单的头插法，试想一下，假如有两个线程A和B都往同一个hashmap中写元素，恰好这两个元素算出来的索引是一样的，B线程执行到`Entry<K,V> e = table[bucketIndex]`后时间片用完，获取了桶中第一个元素后就挂起了，然后线程A进入这个方法并执行完，这时候看似A线程成功将它所操作的元素插入了进来，等到B线程的时间片来临时，B线程继续上次停止的地方执行，因为A线程和B线程获取的是相同的头元素，所以B线程的插入会覆盖之前B线程的操作。

![](https://s2.ax1x.com/2019/09/09/nYFfhj.jpg)

2. 执行resize的时候

执行resize的时候，很容易造成循环链表，使得cpu占用率飙升。上面展示了resize的代码，它有个核心方法transfer:

![](https://s2.ax1x.com/2019/09/09/nYAqfJ.png)

作用就是把原来table中的元素转移到新的table中。留意圈出来的内容，你会发现它其实就是个将当前元素e头插的链表操作.

同样假设有两个线程，假设了我们的hash算法就是简单的用key mod 一下表的大小。

​	 (1) 假设线程一刚好执行完代码1就被挂起，而线程二执行完了，那么情况如下：

![](https://s2.ax1x.com/2019/09/09/nYZFsI.png)

线程一的e指向3，next指向7.

​	(2) 线程一被调度回来执行，执行完当前循环，将3头插，并且执行下次循环中的代码`next=e.next`后，

![](https://s2.ax1x.com/2019/09/09/nYZHk8.png)

​	(3)  将7头插，并执行下一次循环中的`next=e.next`后

![](https://s2.ax1x.com/2019/09/09/nYeVXR.png)

​	(4) 它来了，它带着环型链表来了

![](https://s2.ax1x.com/2019/09/09/nYe534.png)

总结一下，为什么会出现环型链表，针对这个链表而言，是因为我们把链表的最后一个元素进行了头插却没有考虑将指向这个节点的next指针置为null导致的。

3. 执行remove的时候



### `ConcurrentHashMap`

#### 1. jdk 1.7

##### 工作原理

使用分段锁技术，定义了`Segment`类，该类继承自`ReentryLock`, `ConcurrentHashMap`结构大概 如下：

![](https://s2.ax1x.com/2019/09/06/nKEgPK.png)

这相当于一种分治思想，`Segment`数组中的每个元素包含了一个`table`数组,这是一个原始意义上的`HashMap`，每个`table`数组的元素里装了`HashEntry`. `table`整体是一个数组链表的形式。 即使需要加锁，也是对每个段进行加锁。

`HashEntry`所包含的字段如下：

```java
final int hash;
final K key;
volatile V value;
volatile HashEntry<K,V> next;
```

可以发现，`hash`和`key`都是被final修饰的， `value`和`next`是被`volatile`修饰的，保证了多线程下的可见性。



##### put

```java
public V put(K key, V value) {
        Segment<K,V> s;
        if (value == null) //value不能为空
            throw new NullPointerException();
        int hash = hash(key);
        int j = (hash >>> segmentShift) & segmentMask; //寻找对应的段
        if ((s = (Segment<K,V>)UNSAFE.getObject          // nonvolatile; recheck
             (segments, (j << SSHIFT) + SBASE)) == null) //  in ensureSegment
            s = ensureSegment(j);
        return s.put(key, hash, value, false); //在对应的段中进行put
}
```

从上述代码可以发现，`ConcurrentHashMap`中`value`不允许为空。段中的`put`方法如下：

```java
final V put(K key, int hash, V value, boolean onlyIfAbsent) {
            HashEntry<K,V> node = tryLock() ? null :
                scanAndLockForPut(key, hash, value);
            V oldValue;
            try {
                HashEntry<K,V>[] tab = table;
                int index = (tab.length - 1) & hash;
                HashEntry<K,V> first = entryAt(tab, index);
                for (HashEntry<K,V> e = first;;) {
                    if (e != null) {
                        K k;
                        if ((k = e.key) == key ||
                            (e.hash == hash && key.equals(k))) { //如果存在相同entry则替换
                            oldValue = e.value;
                            if (!onlyIfAbsent) {
                                e.value = value;
                                ++modCount;
                            }
                            break;
                        }
                        e = e.next;
                    }
                    else { //如果当前桶里没东西则创建新Entry加进去
                        if (node != null)
                            node.setNext(first);
                        else
                            node = new HashEntry<K,V>(hash, key, value, first);
                        int c = count + 1;
                        if (c > threshold && tab.length < MAXIMUM_CAPACITY)
                            rehash(node);
                        else
                            setEntryAt(tab, index, node);
                        ++modCount;
                        count = c;
                        oldValue = null;
                        break;
                    }
                }
            } finally {
                unlock();
            }
            return oldValue;
        }


```

可以看到put操作还是有加锁处理的，因为volatile关键字并不能保证原子性。先尝试获取锁，如果失败，则利用scanAndLockForPut自旋获取锁。



##### rehash

```java
private void rehash(HashEntry<K,V> node) {
            /*
             * Reclassify nodes in each list to new table.  Because we
             * are using power-of-two expansion, the elements from
             * each bin must either stay at same index, or move with a
             * power of two offset. We eliminate unnecessary node
             * creation by catching cases where old nodes can be
             * reused because their next fields won't change.
             * Statistically, at the default threshold, only about
             * one-sixth of them need cloning when a table
             * doubles. The nodes they replace will be garbage
             * collectable as soon as they are no longer referenced by
             * any reader thread that may be in the midst of
             * concurrently traversing table. Entry accesses use plain
             * array indexing because they are followed by volatile
             * table write.
             */
            HashEntry<K,V>[] oldTable = table;
            int oldCapacity = oldTable.length;
            int newCapacity = oldCapacity << 1;
            threshold = (int)(newCapacity * loadFactor);
            HashEntry<K,V>[] newTable =
                (HashEntry<K,V>[]) new HashEntry[newCapacity];
            int sizeMask = newCapacity - 1;
            for (int i = 0; i < oldCapacity ; i++) {
                HashEntry<K,V> e = oldTable[i];
                if (e != null) {
                    HashEntry<K,V> next = e.next;
                    int idx = e.hash & sizeMask;
                    if (next == null)   //  Single node on list
                        newTable[idx] = e;
                    else { // Reuse consecutive sequence at same slot
                        HashEntry<K,V> lastRun = e;
                        int lastIdx = idx;
                        for (HashEntry<K,V> last = next;
                             last != null;
                             last = last.next) {
                            int k = last.hash & sizeMask;
                            //1. 这里就是遍历当前链表，找到最后一个不在原桶中的元素，那么这个元素后面的所有元素也都不在原桶中。
                            if (k != lastIdx) {
                                lastIdx = k;
                                lastRun = last;
                            }
                        }
                        newTable[lastIdx] = lastRun;
                        // Clone remaining nodes
                        for (HashEntry<K,V> p = e; p != lastRun; p = p.next) {
                            V v = p.value;
                            int h = p.hash;
                            int k = h & sizeMask;
                            HashEntry<K,V> n = newTable[k];
                            newTable[k] = new HashEntry<K,V>(h, p.key, v, n);
                        }
                    }
                }
            }
            int nodeIndex = node.hash & sizeMask; // add the new node
            node.setNext(newTable[nodeIndex]);
            newTable[nodeIndex] = node;
            table = newTable;
        }
```

这里主要要注意里面的一个优化，进行rehash时，由于扩容是二倍，所以本来桶中的那些entry要么在原处，要么在原位置+原容量的位置，也就是说桶中的entry只有两个去处：原地不动或者当前位置+容量。所以注释1处找到最后一个不在原桶中的元素后，这个元素后面的所有元素都不在原桶中且都在相同的索引处。

##### get

```java
public V get(Object key) {
        Segment<K,V> s; // manually integrate access methods to reduce overhead
        HashEntry<K,V>[] tab;
        int h = hash(key);
        long u = (((h >>> segmentShift) & segmentMask) << SSHIFT) + SBASE;
        if ((s = (Segment<K,V>)UNSAFE.getObjectVolatile(segments, u)) != null &&
            (tab = s.table) != null) {
            for (HashEntry<K,V> e = (HashEntry<K,V>) UNSAFE.getObjectVolatile
                     (tab, ((long)(((tab.length - 1) & h)) << TSHIFT) + TBASE);
                 e != null; e = e.next) {
                K k;
                if ((k = e.key) == key || (e.hash == h && key.equals(k)))
                    return e.value;
            }
        }
        return null;
    }
```

因为value都是volatile修饰的，所以get过程不需要加锁。

##### size

size方法是跨段操作

![nYrJ7q.png](https://s2.ax1x.com/2019/09/09/nYrJ7q.png)



#### 2. jdk 1.8

##### 工作原理

底层使用红黑树，类似hashmap的优化：

![](https://s2.ax1x.com/2019/09/09/nYK6RU.jpg)

在并发控制上，抛弃了原本的分段锁，采用CAS+synchronized 来保证并发安全性。



##### put

![](https://s2.ax1x.com/2019/09/09/nYGUfI.png)

##### get

![](https://s2.ax1x.com/2019/09/09/nYYdL8.png)



##### size方法

1.8中size方法就比较简单

```java
public int size() {
        long n = sumCount();
        return ((n < 0L) ? 0 :
                (n > (long)Integer.MAX_VALUE) ? Integer.MAX_VALUE :
                (int)n);
    }
```

sumCount方法：

```java
final long sumCount() {
        CounterCell[] as = counterCells; CounterCell a;
        long sum = baseCount;
        if (as != null) {
            for (int i = 0; i < as.length; ++i) {
                if ((a = as[i]) != null)
                    sum += a.value;
            }
        }
        return sum;
    }
```

如果counterCells不空，则遍历元素和baseCount累加。关于baseCount和CounterCells解释如下：

baseCount定义如下：

```java
/**
 * Base counter value, used mainly when there is no contention,
 * but also as a fallback during table initialization
 * races. Updated via CAS.
 */
private transient volatile long baseCount;
```

通过CAS更新，没有争用时使用它计数。它在addCount方法中被使用。

如果有争用，baseCount的CAS更新失败，那么就尝试把要更新的增量更新到CounterCell中

![nYLb9O.png](https://s2.ax1x.com/2019/09/09/nYLb9O.png)

CounterCell结构如下：

```java
/**
     * A padded cell for distributing counts.  Adapted from LongAdder
     * and Striped64.  See their internal docs for explanation.
     */
    @sun.misc.Contended static final class CounterCell {
        volatile long value;
        CounterCell(long x) { value = x; }
    }
```

#### 1.7和1.8的区别

|          | 1.7                      | 1.8                   |      |
| -------- | ------------------------ | --------------------- | ---- |
| 数据结构 | 链表                     | 红黑树                |      |
| 并发控制 | 分段锁                   | CAS+synhcronized      |      |
| size     | 多次计算，再决定是否加锁 | baseCount+CounterCell |      |



### 参考

[Map 综述（三）：彻头彻尾理解 ConcurrentHashMap](<https://blog.csdn.net/justloveyou_/article/details/72783008>)（jdk 1.6）

[HashMap? ConcurrentHashMap? 相信看完这篇没人能难住你！](<https://juejin.im/post/5b551e8df265da0f84562403>) (jdk1.7 jdk 1.8)

[Java进阶（六）从ConcurrentHashMap的演进看Java多线程核心技术](<http://www.jasongj.com/java/concurrenthashmap/>)

[疫苗：JAVA HASHMAP的死循环](<https://coolshell.cn/articles/9606.html>)

[并发编程 —— ConcurrentHashMap size 方法原理分析](<https://juejin.im/post/5ae75584f265da0b873a4810>)

