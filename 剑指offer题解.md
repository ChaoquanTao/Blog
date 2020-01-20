---
title: 剑指offer题解
date: 2019-09-15 17:25:15
updated: 2019-09-15 17:25:15
tags: 剑指offer
categories: 数据结构与算法
---

## 重建二叉树

前序遍历用来确定根节点，中序遍历用来确定左右子树以及大小

```java
class TreeNode {
    int val;
    TreeNode left;
    TreeNode right;

    TreeNode(int x) {
        val = x;
    }
}
public class ReconsBinTree {
    public static void main(String[] args) {
        int[] pre={1,2,4,7,3,5,6,8};
        int[] in = {4,7,2,1,5,3,6,8};

        TreeNode root = reConstructBinaryTree(pre,in);
//        System.out.println(root);
        lastOrder(root);
    }



    //前序遍历提供跟节点，中序遍历提供切分以及左右子树的大小
    public static TreeNode reConstructBinaryTree(int[] pre, int[] in) {

//        TreeNode root = new TreeNode(pre[0]);
        TreeNode root = reconstruct(pre[0],pre,0,pre.length,in,0,in.length);

        return root;

    }

    public static TreeNode reconstruct(int rootVal,int[] pre,int preStart,
                                       int preEnd, int[] in, int inStart, int inEnd){

        TreeNode root = new TreeNode(rootVal);
        int rootIdxAtPre = getIndex(pre,preStart,preEnd,root.val) ;
        int rootIdxAtIn = getIndex(in,inStart,inEnd,root.val);

        if(rootIdxAtIn>0){ //说明有左孩子，索引以左就是左孩子
            int lidx = rootIdxAtPre+1;
//            TreeNode left = new TreeNode(pre[preStart+lidx]);
//            root.left=left;

            root.left = reconstruct(pre[preStart+lidx],pre,preStart+1,preStart+1+rootIdxAtIn,in,inStart,inStart+rootIdxAtIn);
        }
        else
            root.left=null;

        if(inStart+rootIdxAtIn<inEnd-1){
            int ridx = rootIdxAtIn+1;
//            TreeNode right = new TreeNode(pre[preStart+ridx]);
//            root.right=right;

            root.right = reconstruct(pre[preStart+ridx], pre,preStart+rootIdxAtIn+1,preEnd,in,inStart+rootIdxAtIn+1,inEnd);
        }
        else
            root.right=null;
        return root;
    }

    //返回相对位置索引
    public static int getIndex(int[] arr, int start, int end, int val){
        for(int i=start; i<end; i++){
            if(arr[i]==val)
                return i-start;
        }
        return -1;
    }

    //后续遍历测试
    public static void lastOrder(TreeNode root){
        if(root!=null) {
            if (root.left != null)
                lastOrder(root.left);
            if (root.right != null)
                lastOrder(root.right);
        }

        System.out.println(root.val);
    }


}
```

## 用两个栈实现队列

```java
import java.util.Stack;

/**
 * 思路：从stack1 push,从stack2 pop.
 */
public class Stack2Q {
    static Stack<Integer> stack1 = new Stack<Integer>();
    static Stack<Integer> stack2 = new Stack<Integer>();

    public static void push(int node) {
        stack1.push(node) ;
    }

    public static int pop() {
        int node ;
        //stack2中有的话直接pop
        if(!stack2.isEmpty()){
            node = stack2.pop();
        }
        else {//没有的话先从stack1转移到stack2
            while (!stack1.isEmpty()){
                int tnode = stack1.pop();
                stack2.push(tnode);
            }
            node = stack2.pop();
        }
        return node ;
    }

    public static void main(String[] args) {
        push(1);
        push(2);
        push(3);
        push(4);

        System.out.println(pop());
        System.out.println(pop());
    }
}
```

## 旋转数组的最小数字

```java
/**
 * 利用旋转数组的特性，使用二分查找：
 * 如果中间数大于array[start]且大于array[end],区后半段
 * 如果中间数大于array[start]且小于array[end]，取前半段
 * 如果中间数小于array[start]，取前半段
 * 
 * 需要注意下标的取法
 */
public class MinNumInRotateArray {

    public static int minNumberInRotateArray(int[] array) {
        int min = binSearch(array,0,array.length-1);
        return min;
    }

    static int  binSearch(int[] arr, int start, int end){
        int res;
        if(end-start<=0){
            res = arr[start];
            return res;
        }
        int mid = (start+end)/2;
        if(arr[mid]>=arr[start] && arr[mid] >=arr[end] ){
            res = binSearch(arr,mid+1,end);//后面
        }
        else {
            res = binSearch(arr,start,mid);//前面
        }
        return res;

    }

    public static void main(String[] args) {
        int[] array={3,4,5,1,2};
        System.out.println(minNumberInRotateArray(array));
    }
}

```

## 跳台阶

一道典型的动态规划问题，对于跳上第n个台阶，只有两种跳法：

+ 从第n-1个台阶跳一步上去
+ 从第n-2个台阶跳两步上去

所以我们有

$$ f(n)=\left\{
\begin{aligned}
&1 & n=1 \\
&2 & n=2 \\
&f(n-1)+f(n-2) & n \ge 3
\end{aligned}
\right.$$

其实就是个`Fibonaci`数列，可以用递归求解，但是太麻烦，我们用DP来求解



### 数组版

```java
public class JumpFloor {
//
public static int JumpFloor(int target) {
    if(target==1){
        return 1;
    }
    if(target==2){
        return 2;
    }
    int[] dp = new int[target+1];
    dp[1]=1;
    dp[2]=2;
    for (int i=3; i<=target; i++){

        dp[i]=dp[i-1]+dp[i-2];
    }
    return dp[target];
}

    public static void main(String[] args) {
        System.out.println(JumpFloor(3));
        System.out.println(JumpFloor(4));
    }
}

```



### 精简版

```java
public class JumpFloor {
    public static int JumpFloor(int target) {
        if(target==1){
            return 1;
        }
        if(target==2){
            return 2;
        }
        int pre=1,cur=2,res=0;
        for(int i=3; i<=target; i++){
            res = pre+cur;
            pre=cur;
            cur=res;
        }
        return res;
    }

    public static void main(String[] args) {
        System.out.println(JumpFloor(3));
        System.out.println(JumpFloor(4));
    }
}
```



## 变态跳台阶

题目描述:

一只青蛙一次可以跳上1级台阶，也可以跳上2级……它也可以跳上n级。求该青蛙跳上一个n级的台阶总共有多少种跳法。

解析：

同样的，先写出递归方程，然后用递归或者DP来求解。

相比于上面那一道普通跳台阶，这里只不过是能跳的台阶多了一些。



### 矩形覆盖

#### 题目描述

我们可以用2*1的小矩形横着或者竖着去覆盖更大的矩形。请问用n个2*1的小矩形无重叠地覆盖一个2*n的大矩形，总共有多少种方法？

#### 解析

同样的，先写状态转移方程：

$$ f(n)=\left\{
\begin{aligned}
&1 & n=1 \\
&2 & n=2 \\
&f(n-1)+f(n-2) & n \ge 3
\end{aligned}
\right.$$

依然是个斐波那契数列问题

可以用递归和DP解决

> 其实讲道理，我觉得这道题也可以用排列组合来求解的

#### 代码

```java
 public int RectCover(int target) {
        if (target == 1)
            return 1;
        if (target == 2)
            return 2;
        return RectCover(target - 1) + RectCover(target - 2);
    }
```

DP:

```java
 public int RectCover(int target) {
        int sum,p1,p2 ;
        if(target <=0)
            return 0;
        if (target == 1)
            return 1;
        if (target == 2)
            return 2;
        p1=1;
        p2=2;
        sum=0;
        for (int i = 3; i<=target; i++){
            sum = p1 +p2 ;
            p1 = p2 ;
            p2 = sum ;
        }
        return sum;
    }
```

### 二进制中1的个数

#### 题目描述

 输入一个整数n，输出该数二进制表示中1的个数。其中负数用补码表示。 

#### 解析

方法一： 无符号右移输入的数字，然后和1逻辑与

方法二：保持输入不动，每次右移数字1然后逻辑与

方法三：将n和n-1逻辑与，消除一个n最右边的数字1

#### 代码

方法一：

```java
public class NumberOf1 {
    public int NumberOf1(int n) {
        int count = 0;
        while (n!=0){
            count += (n&1) ;
            n = n>>>1;
        }
        return count;
    }

    public static void main(String[] args) {
        System.out.println(new NumberOf1().NumberOf1(0x80000000));
    }
}

```



### 数值的整数次方

#### 题目描述

给定一个double类型的浮点数base和int类型的整数exponent。求base的exponent次方。

保证base和exponent不同时为0

#### 解析

1. 方法一：for循环暴力输出，需要考虑到指数为负数等边界情况
2. 方法二：使用递归将指数拆解进行计算。



### 调整数组顺序使奇数位于偶数前面

#### 题目描述

输入一个整数数组，实现一个函数来调整该数组中数字的顺序，使得所有的奇数位于数组的前半部分，所有的偶数位于数组的后半部分，并保证奇数和奇数，偶数和偶数之间的相对位置不变。

#### 解析

这个问题使用冒泡排序的思想也可以解决，相邻元素比较并交换，问题在于这样做的话无谓的比较和交换比较多。比如说有一长串都是奇数或者偶数，这种情况我们就可以跳过了，其实是有点类似与KMP算法的。

所以我们需要两个指针，一个指向当前出现的第一个偶数，一个指向第一个偶数出现后的第一个奇数，然后奇数放在偶数位，偶数们依次后移。



#### 代码

```java
 public void reOrderArray(int [] array) {
        int feven=0; //第一个偶数的位置
        int fodd=1; // 第一个偶数后第一个奇数的位置
        int i=0;
        if(array==null || array.length==1)
            return ;
        while(fodd<=array.length){
            for(; feven<array.length; feven++){ //寻找第一个偶数的位置
                if(isEven(array[feven])){

                    break;
                }
            }
            for(fodd=feven+1; fodd<array.length; fodd++){//找到偶数后第一个奇数的位置
                if(!isEven(array[fodd])){

                    break;
                }
            }
            if(fodd>=array.length)
                break;
            int t = array[fodd] ;
            for(int j = fodd-1; j>=feven; j--){
                array[j+1] = array[j];
            }
            array[feven] = t ;


        }

    }

    public boolean isEven(int e){
        return e%2==0 ;
    }
```

或者

```java
public class Solution {
    public void reOrderArray(int [] array) {
       for(int i= 0;i<array.length-1;i++){
            for(int j=0;j<array.length-1-i;j++){
                if(array[j]%2==0&&array[j+1]%2==1){
                    int t = array[j];
                    array[j]=array[j+1];
                    array[j+1]=t;
                }
            }
        }
    }
}
```

很类似于冒泡排序，每一轮冒泡保证至少有一个元素归位。

其实就是个冒泡排序，只不过我们常见的冒泡排序里面比较的是元素大小，这里比较的是元素奇偶，还有很重要的一点就是冒泡排序是稳定的，对应到题目中就是**保证奇数和奇数，偶数和偶数之间的相对位置不变**。

这里相当于是一个通用性的冒泡排序，至于按照什么条件进行相邻元素比较是可插拔的，实在是妙啊。

所以理论上讲，这道题只要是稳定的排序算法应该是都可以用的。

那哪些排序稳定哪些排序不稳定呢？

一言以蔽之：涉及到非相邻交换的排序都是不稳定的，比如选择排序，比如快速排序，希尔排序，比如堆排序。



### 链表中倒数第k个结点

#### 题目描述

输入一个链表，输出该链表中倒数第k个结点。



#### 分析

用标尺法就可以解决。

#### 代码

```java
/*
public class ListNode {
    int val;
    ListNode next = null;

    ListNode(int val) {
        this.val = val;
    }
}*/
public class Solution {
    public ListNode FindKthToTail(ListNode head,int k) {
		ListNode cur = head ;
        if(head == null){
            return null ;
        }
        if(k==0){
            return null; 
        }
        ListNode post = cur.next ;
        int i = 1 ;
        while(post != null && i<k){
            post = post.next ;
            i++;
        }
        if(i<k){
            return null ;
        }
        while(post !=null){
            cur = cur.next;
            post = post.next ;
        }
        return cur ;
    }
}
```

