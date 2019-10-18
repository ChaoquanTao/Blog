---
title: Map中的hash方法
date: 2019-10-08 20:50:13
updated: 2019-10-08 20:50:13
tags: 集合类
categories: Java
---

在`HashMap`,`HashTable`和`ConcurrentHashMap`中，`hash()`方法主要是拿来做定位，即通过对key进行散列，从而确定这个entry的存储位置。但是为了避免发生碰撞，java中的hash方法还是有许多细节操作的。

### `HashMap`

#### jdk 7

代码如下：

```java
final int hash(Object k) {
        int h = hashSeed;
        if (0 != h && k instanceof String) {
            return sun.misc.Hashing.stringHash32((String) k);
        }

        h ^= k.hashCode();

        // This function ensures that hashCodes that differ only by
        // constant multiples at each bit position have a bounded
        // number of collisions (approximately 8 at default load factor).
        h ^= (h >>> 20) ^ (h >>> 12);
        return h ^ (h >>> 7) ^ (h >>> 4);
    }
```

```java
static int indexFor(int h, int length) {
        // assert Integer.bitCount(length) == 1 : "length must be a non-zero power of 2";
        return h & (length-1);
    }
```

上述代码中，`hash()`方法负责生成哈希码，`indexFor()`方法负责确定地址。可以看到，哈希码的生成主要通过随机种子和`hashCode`进行异或，后面的两行代码是为了进行混淆。因为最终索引（存储地址）是通过哈希码取模数组长度得到的，这意味着只有有限比特位（length-1 个比特位）会影响到最终结果，混淆的作用就是为了尽力让哈希码的每个位置在确定索引时都发挥作用。

说到这里，请留意下`hashCode`方法，这是Object类的一个native方法，返回的是对象的地址，在`HashMap`中被重写了

```java
public final int hashCode() {
     return Objects.hashCode(getKey()) ^ Objects.hashCode(getValue());
}

```

当然equals方法也被重写了，这里就不再赘述。



#### jdk 8

```
static final int hash(Object key) {
        int h;
        return (key == null) ? 0 : (h = key.hashCode()) ^ (h >>> 16);
    }
```

直接拿hashCode和高16位异或。

### HashTable 

#### jdk 7

相比于HashMap，HashTable是线程安全的，而且它的hash方法也显得很朴实无华，没有添加扰动，

```java
private int hash(Object k) {
        // hashSeed will be zero if alternative hashing is disabled.
        return hashSeed ^ k.hashCode();
    }
```

它没有indexFor方法，取而代之的是一句代码

```java
int index = (hash & 0x7FFFFFFF) % tab.length;
```

为什么没加扰动呢，我是这么考虑的。

> 从性能角度考虑，`HashMap`采用2的次幂作为容量有一部分是出于性能考虑，使用2的次幂后，无论是扩容还是`indexFor`,都可以通过位运算加快运算速度。
>
> 而`HashTable`通过`synchronized`关键字来保证线程安全，它在性能上已经落后`HashMap`了，所以对2的次幂要求不是很高。再者，`HashTable`初始容量为11，按照$2n+1$扩容，容量一直是素数，而这个素数恰好能使得在取模的过程中让key分散均匀一些，所以也就没有加扰动。
>
> 

#### jdk 8

```java
int hash = key.hashCode();
int index = (hash & 0x7FFFFFFF) % tab.length;
```

分别将hash方法和indexFor方法变成了两句话。（可以看到1.8中HashMap和HashTable都摒弃了hashSeed.

### `ConcurrentHashMap`

#### jdk 7

```java
private int hash(Object k) {
        int h = hashSeed;

        if ((0 != h) && (k instanceof String)) {
            return sun.misc.Hashing.stringHash32((String) k);
        }

        h ^= k.hashCode();

        // Spread bits to regularize both segment and index locations,
        // using variant of single-word Wang/Jenkins hash.
        h += (h <<  15) ^ 0xffffcd7d;
        h ^= (h >>> 10);
        h += (h <<   3);
        h ^= (h >>>  6);
        h += (h <<   2) + (h << 14);
        return h ^ (h >>> 16);
    }
```

和`HashMap`中做法差不多，只不过加的不是同一种扰动。

#### jdk 8



```java
    static final int spread(int h) {
        return (h ^ (h >>> 16)) & HASH_BITS;
    }

```

愈发简洁，参考1.8中的HashMap,和高16位异或，然后与了HASH_BITS,主要是为了防止出现负数。

```java
    static final int HASH_BITS = 0x7fffffff; // usable bits of normal node hash
```



可以看到，1.8中HashMap和ConcurrentHashMap的hash设计都简单了许多，其实一定程度上也和红黑树的引入有关系，1.8版本引入了红黑树，在一定程度上降低了哈希冲突后的检索耗时，所以在散列的尽可能均匀上下功夫不多。

### 参考

[全网把Map中的hash()分析的最透彻的文章，别无二家](https://www.hollischuang.com/archives/2091)