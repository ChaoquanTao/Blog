---
title: 剑指offer题解
date: 2019-09-15 17:25:15
updated: 2019-09-15 17:25:15
tags: 剑指offer
categories: 题解
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